from antlr4 import FileStream, CommonTokenStream
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from sv_parser.visitor import lower_stmt_to_logic_tree
from logictree.nodes import ops, control, base, hole
from logictree.utils.display import pretty_print
import logging
log = logging.getLogger(__name__)
AssignStmtCtxtClass = SystemVerilogSubsetParser.Continuous_assignContext
IfStmtCtxtClass = SystemVerilogSubsetParser.If_statementContext
Expression_listCtxClass = SystemVerilogSubsetParser.Expression_listContext

class SVToLogicTreeLowerer(SystemVerilogSubsetVisitor):
    def __init__(self):
        super().__init__()
        self.signal_map = {}
        self.output_signals = set()
        self.module_name = None

    def collect_signals(self, tree):
        """Traverse the AST and collect logic trees for each assign or procedural signal."""
        self.visit(tree)
        return self.signal_map

    def lower(self, ast):
        assert isinstance(ast, dict) and ast.get("modules"), "Expected a parsed AST with modules"
        mod = ast["modules"][0]  # just the first module for now

        if not mod["items"]:
            return None

        items = mod["items"][0]
        if not items:
            return None

        stmt = items[0]
        return self.lower_stmt(stmt)

    def flatten_stmt(self, stmt):
        # If we have a list with one item, unwrap it
        if isinstance(stmt, list) and len(stmt) == 1:
            return stmt[0]
        return stmt
    
        def lower_stmt(self, stmt):
            if isinstance(stmt, base.LogicTreeNode):
                return stmt
    
            if stmt["type"] == "if":
                cond = stmt["cond"]
                then_branch = self.lower_stmt(stmt["then"])
                else_branch = self.lower_stmt(stmt["else"])
                return ops.LogicOp("MUX", [cond, then_branch, else_branch])
    
            raise ValueError(f"Unsupported statement type: {stmt}")
        
    def extract_lhs_signal(self, ctx):
        """
        Extracts the left-hand side signal name from an assign_stmt.
        Assumes: assign identifier = expr ;
        """
        if ctx is None:
            return None
        try:
            if hasattr(ctx, "variable_lvalue"):
                lhs = ctx.variable_lvalue()
                if lhs is not None:
                    return lhs.getText()
            if hasattr(ctx, "Identifier"):
                return ctx.Identifier().getText()
            elif hasattr(ctx, "identifier"):
                return ctx.identifier().getText()
            
            if hasattr(ctx, "blocking_assignment") and ctx.blocking_assignment():
                return ctx.blocking_assignment().Identifier().getText()

            child = ctx.getChild(0)
            if hasattr(child, "Identifier"):
                return child.Identifier().getText()

            log.warning(f"Could not extract identifier from context: {type(ctx)}")
            return None
        except Exception as e:
            log.warning(f"Failed to extract LHS from ctx: {type(ctx)} - {e}")
        except AttributeError:
            log.warning(f"Could not extract identifier from context: {type(ctx)}")
            return None

    def visitCompilation_unit(self, ctx):
        # For now, just visit the first module
        return self.visit(ctx.module_declaration(0))

    def visitModule_declaration(self, ctx):
        from logictree.utils.display import pretty_inline
        log.debug("visiting module_declaration")

        # Clear maps at start of module
        self.signal_map = {}
        self.output_signals = set()

        identifier_ctx = ctx.module_identifier()
        if identifier_ctx:
            self.module_name  = identifier_ctx.getText()
        else:
            self.module_name = "unknown module"
        # Visit children (this will trigger port and assign visits)
        result = self.visitChildren(ctx)

        # Output debug summaries
        log.debug("Signal map contents after visiting module:")
        for name, tree in self.signal_map.items():
            log.debug(f" {name}: {tree}")

        log.debug("Output signals detected:")
        for out in self.output_signals:
            log.debug(f"  {out}")
        
        # Select output signal’s tree for return, if available
        for out in self.output_signals:
            if out in self.signal_map:
                log.debug(f"Returning tree for output signal: {out}")
                return self.signal_map[out]

        log.debug(f"Returning tree object id={id(self.signal_map['delivery_confirmed'])}")
        log.debug(f"Expected structure: {pretty_inline(self.signal_map['delivery_confirmed'])}")
        
        # Fallback: return first tree
        log.debug("No matching output found, returning first signal in map.")
        return next(iter(self.signal_map.values())) if self.signal_map else None

    def visitModule_item(self, ctx):
        log.debug("visitModule_item")
        return self.visitChildren(ctx)

    def visitPort_list(self, ctx):
        log.debug("visitPort_list")
        for port_ctx in ctx.port():
            self.visitPort(port_ctx)

    def visitPort(self, ctx):
        log.debug("visitPort")
        children = list(ctx.getChildren())
        if not children:
            return
        direction = children[0].getText()
        if direction == "output":
            # Identifier is always the last child
            identifier = children[-1].getText()
            self.output_signals.add(identifier)
            log.debug(f"Detected output signal: {identifier}")

    def visitAlways_comb_block(self, ctx):
        log.debug("vistAlways_comb_block")
        block = ctx.statement()
        if block is not None:
            log.debug("block: %s", block.getText())
            return self.visit(block)

    def visitStatement_item(self, ctx):
        if ctx.case_statement():
            log.debug("visitStatement_item case_statement!")
            return self.visit(ctx.case_statement())
        if ctx.if_else_if_chain():
            return self.visit(ctx.if_else_if_chain())
        if ctx.non_blocking_assignment():
            return self.visit(ctx.non_blocking_assignment())
        if ctx.blocking_assignment():
            return self.visit(ctx.blocking_assignment())
        # You might also want to support begin-end blocks
        if ctx.statement():
            return self.visit(ctx.statement())
        return None

    def visitStatement(self, ctx):
        log.debug(f"visitStatement() - ctx: {ctx.getText()}")
        if ctx.begin_end_block():
            log.debug("visitStatement begin_end_block")
            block = ctx.begin_end_block()
            results = []
            for stmt in block.statement():
                result = self.visit(stmt)
                results.append(result)
            # Return last assignment result
            return results[-1] if results else (None, None)

        elif ctx.if_statement():
            log.debug("visitStatement if_statement")
            return self.visit(ctx.if_statement())

        elif ctx.case_statement():
            log.debug("visitStatement case_statement")
            case_node = self.visit(ctx.case_statement())
            if isinstance(case_node, control.CaseStatement):
                # Extract LHS from teh first case item (assumes consistemnt assignment target)
                lhs = case_node.items[0].body.lhs
                self.signal_map[lhs] = case_node
                log.debug(f"Registered logic for {lhs}:\n{pretty_print(self.signal_map[lhs])}")
                #log.debug(pretty_print(case_node))
            return case_node

        elif ctx.blocking_assignment():
            log.debug("visitStatement blocking_assigment")
            assign_ctx = ctx.blocking_assignment()
            lhs_name   = assign_ctx.variable_lvalue().getText()
            lhs        = lhs_name
            rhs_expr   = assign_ctx.expression()
            rhs_tree   = self.visit(rhs_expr)
            assign_node  = control.LogicAssign(lhs=lhs, rhs=rhs_tree)
            self.signal_map[lhs] = rhs_tree
            log.info(f"[statement assign] {assign_node}")
            return assign_node
            #return lhs, stmt_tree 

        elif ctx.expression():
            log.debug("visitStatement expression: %s", ctx.expression().getText())
            return self.visit(ctx.expression())
        else:
            log.warning(f"Error unknown statement context: {type(ctx)}")
            #return hole.LogicHole("unhandled_stmt")
            return None, None

    def visitBlocking_assignment(self, ctx):
        log.debug("visitBlocking_assignment")
        lhs = ctx.variable_lvalue().getText()
        rhs = ctx.expression()
        logic_tree = lower_stmt_to_logic_tree(rhs)
        self.signal_map[lhs] = logic_tree
        log.debug(f"[assign] {lhs} = {logic_tree}")
        return logic_tree

    def visitIf_statement(self, ctx):
        log.debug("DEBUG: visitIf_statement()")
        cond_tree = self.visit(ctx.expression())
    
        then_stmt_ctx = ctx.statement(0)
        else_stmt_ctx = ctx.statement(1) if ctx.ELSE() else None
    
        then_result = self.visit(then_stmt_ctx)
        if not isinstance(then_result, control.LogicAssign):
            raise TypeError(f"Expected LogicAssign from then-branch, got {type(then_result)}")
        lhs_then = then_result.lhs
        then_tree = then_result.rhs
    
        if else_stmt_ctx:
            else_result = self.visit(else_stmt_ctx)
            if not isinstance(else_result, control.LogicAssign):
                raise TypeError(f"Expected LogicAssign from else-branch, got {type(else_result)}")
            lhs_else = else_result.lhs
            else_tree = else_result.rhs
        else:
            lhs_else = lhs_then
            else_tree = ops.LogicConst(0)
    
        if lhs_then != lhs_else:
            raise NotImplementedError("Mismatched lhs in if/else assignment")
    
        mux_tree = ops.LogicOp("MUX", [cond_tree, then_tree, else_tree])
        self.signal_map[lhs_then] = mux_tree
        return control.LogicAssign(lhs_then, mux_tree)

    def visitContinuous_assign_statement(self, ctx):
        log.debug("visitContinuousAssign_statement")
        expr_ctx   = ctx.expr()
        logic_tree = lower_stmt_to_logic_tree(expr_ctx)
        lhs_signal = self.extract_lhs_signal(ctx)
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree
            
    def visitContinuous_assign(self, ctx):
        log.debug("visitContinuous_assign")
        expr_ctx   = ctx.expression()
        logic_tree = self.visit(expr_ctx)
        lhs_signal = self.extract_lhs_signal(ctx)
        from logictree.utils.display import pretty_inline
        logic_tree.set_viz_label(f"{lhs_signal} = {pretty_inline(logic_tree)}")
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree

    def visitAssign_statement(self, ctx):
        log.debug("visitAssign_statement")
        expr_ctx   = ctx.expr()
        logic_tree = lower_stmt_to_logic_tree(expr_ctx)
        lhs_signal = self.extract_lhs_signal(ctx)
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree

    def visitCase_statement(self, ctx):
        # Get the switch expression
        switch_expr_ctx = ctx.expression()
        switch_tree = self.visit(switch_expr_ctx)
    
        # Create a CaseStatement LogicTreeNode wrapper
        case_node = control.CaseStatement(selector=switch_tree, items=[])
    
        for item_ctx in ctx.case_item():
            if item_ctx.DEFAULT():
                label_exprs = ['default']
            else:
                label_exprs = [self.visit(e) for e in item_ctx.expression_list().expression()]
    
            stmt_ctx = item_ctx.statement()
            stmt_tree = self.visit(stmt_ctx)
    
            case_item = control.CaseItem(labels=label_exprs, body=stmt_tree)
            case_node.items.append(case_item)
    
        # Store CaseStatement in a temporary logic tree hole (for now)
        return case_node

    def visitExpression(self, ctx):
        log.debug("visitExpression")
        if ctx.getChildCount() == 1:
            if ctx.identifier():
                log.debug(f"visitExpression -> LogicVar: {ctx.getText()}")
                return ops.LogicVar(ctx.getText())
            if ctx.literal():
                const = self.visitLiteral(ctx.literal())
                log.debug(f"visitExpression -> Const: {const}")
                return const

        elif ctx.getChildCount() == 2:  # Unary (e.g. ~a)
            op = ctx.getChild(0).getText()
            rhs = self.visit(ctx.getChild(1))
            log.debug(f"Unary op '{op}' on {rhs}")
            if op == '~':
                log.debug(f"visitExpression() self.name: {self.name}, rhs: {rhs}")
                return ops.LogicOp("NOT", [rhs])

        elif ctx.getChildCount() == 3:
            lhs = self.visit(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            rhs = self.visit(ctx.getChild(2))
            log.debug(f" Binary '{op}': lhs={lhs}, rhs={rhs}")

            if op == '&':  return ops.LogicOp("AND", [lhs, rhs])
            if op == '|':  return ops.LogicOp("OR", [lhs, rhs])
            if op == '^':  return ops.LogicOp("XOR", [lhs, rhs])
            if op == '~^': return ops.LogicOp("XNOR", [lhs, rhs])
            if op == '==':
                if isinstance(rhs, list):
                    log.debug(f"Expanding bitvector comparison: {lhs} == {rhs}")
                    return ops.LogicOp("AND", [
                        ops.LogicOp("XNOR", [ops.LogicVar(f"{lhs.name}_{i}"), ops.LogicConst(bit)])
                        for i, bit in enumerate(rhs)
                    ])
                else:
                    return ops.LogicOp("XNOR", [lhs, rhs])

        elif ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(':
            log.debug("Parenthesized expression")
            return self.visit(ctx.getChild(1))  # Parenthesized

        raise NotImplementedError("Unhandled expression structure: " + ctx.getText())

    def visitLogicalNotExpr(self, ctx):
        log.debug("visitLogicalNotExpr")
        expr = self.visit(ctx.expression())
        return ops.LogicOp("NOT", [expr])

    def visitBitwiseNotExpr(self, ctx):
        log.debug("visitBitwiseNotExpr")
        expr = self.visit(ctx.expression())
        return ops.LogicOp("NOT", [expr])  # or differentiate if needed

    def visitNegateExpr(self, ctx):
        log.debug("visitNegateExpr")
        expr = self.visit(ctx.expression())
        # Treat -a as NOT(a) for logic, or raise NotImplementedError if arithmetic
        return ops.LogicOp("NOT", [expr])

    def visitAndExpr(self, ctx):
        log.debug("visitAndExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.LogicOp("AND", [lhs, rhs])

    def visitOrExpr(self, ctx):
        log.debug("visitOrExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.LogicOp("OR", [lhs, rhs])

    def visitXorExpr(self, ctx):
        log.debug("visitXorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.LogicOp("XOR", [lhs, rhs])

    def visitXnorExpr(self, ctx):
        log.debug("visitXnorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.LogicOp("XNOR", [lhs, rhs])

    def visitEqExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        log.debug("visitEqExpr with: lhs: {%s}, rhs: {%s}", lhs, rhs)
        log.debug("rhs type: %s",  type(rhs))

        # Case 1: Bitvector comparison against a constant like 7'b0110011
        #if isinstance(rhs, ops.LogicConst) and isinstance(lhs, LogicHole):
        if isinstance(rhs, list):
            log.debug("visitEqExpr Found a bitvector comparison agains constant")
            # Try to parse bitvector pattern from the original token
            rhs_text = ctx.expression(1).getText()
            if "'" in rhs_text:  # e.g., 7'b0110011
                try:
                    width_str, value_str = rhs_text.split("'")
                    base = value_str[0].lower()
                    bits = value_str[1:]  # Just the bit pattern

                    if base != 'b':
                        raise NotImplementedError("Only binary constants like 7'b0101 are supported")

                    xnor_terms = []
                    for i, bit_char in enumerate(bits[::-1]):  # LSB first
                        bit_val = 1 if bit_char in ('1', 'x') else 0  # 'x' gets mapped to 1 for analysis
                        var = ops.LogicVar(f"{lhs.name}_{i}")
                        xnor = ops.LogicOp("XNOR", [var, ops.LogicConst(bit_val)])
                        xnor_terms.append(xnor)

                    if len(xnor_terms) == 1:
                        return xnor_terms[0]
                    else:
                        # Recursively reduce with ANDs
                        from logictree.utils import balanced_tree_reduce
                        return balanced_tree_reduce("AND", xnor_terms)

                except Exception as e:
                    log.error(f"Failed to parse bitvector comparison: {rhs_text}")
                    raise e

        # Case 2: Simple variable == variable or constant
        return ops.LogicOp("XNOR", [lhs, rhs])

    def visitParenExpr(self, ctx):
        log.info("visitParenExpr with: %s", ctx.getText())
        return self.visit(ctx.expression())

    def visitLiteral(self, ctx):
        log.debug("visitLiteral")
        raw = ctx.getText()
        if "'" in raw:
            # binary constatn like 7'b0110011
            bits = text.split("'")[1][1:]
            #bits = [int(b) for b in raw.split("'")[1][1:]]
            return [int(b) for b in bits]
            #return ops.LogicConst(bits)  # for == bitvector case
        else:
            return ops.LogicConst(int(raw))

    def visitConstExpr(self, ctx):
        log.info("visitConstExpr with: %s", ctx.getText())
        text = ctx.getText()
        if "'" in text:
            # Format: 7'b0110011 or similar
            try:
                width_str, base_and_value = text.split("'")
                width = int(width_str)
                base = base_and_value[0].lower()
                value = base_and_value[1:]
    
                if base == 'b':
                    bits = [int(b) for b in value]
                    return bits
                else:
                    raise NotImplementedError(f"Base '{base}' not supported")
            except Exception as e:
                log.warning(f"Failed to parse bitvector constant: {text} with error: {e}")
                return hole.LogicHole(text)
        else:
            # Just a number like `1` or `0`
            return ops.LogicConst(int(text))

    def visitIdExpr(self, ctx):
        log.info("visitIdExpr with: %s", ctx.getText())
        return ops.LogicVar(ctx.getText())

