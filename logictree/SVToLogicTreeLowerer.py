from antlr4 import FileStream, CommonTokenStream
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from logictree.nodes import LogicNode, LogicVar, LogicConst, LogicOp, LogicHole, NotOp
import logging
log = logging.getLogger(__name__)
AssignStmtCtxtClass = SystemVerilogSubsetParser.Continuous_assignContext
LOGIC_NODE_TYPES = (LogicHole, LogicVar, LogicConst, LogicOp, NotOp)

class SVToLogicTreeLowerer(SystemVerilogSubsetVisitor):
    def __init__(self):
        self.logic_by_signal = {}  # Collect (signal_name → LogicTree)

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

    def lower_stmt(self, stmt):
        if isinstance(stmt, LogicNode):
            return stmt

        if stmt["type"] == "if":
            cond = stmt["cond"]
            then_branch = self.lower_stmt(stmt["then"])
            else_branch = self.lower_stmt(stmt["else"])
            return LogicOp("MUX", [cond, then_branch, else_branch])

        raise ValueError(f"Unsupported statement type: {stmt}")
    
    def lower_file(self, filepath):
        # 1. REad and lex/parse the SystemVerilog source
        with open(filepath, 'r') as f:
            code = f.read()

        input_stream = FileStream(filepath)
        lexer = SystemVerilogSubsetLexer(input_stream)
        tokens = CommonTokenStream(lexer)
        parser = SystemVerilogSubsetParser(tokens)
        tree = parser.compilation_unit()

        # 2. Optionally return to ast
        # ast = ASTBuilder().visit(tree)

        # 3. Convert to LogicTree IR
        return self.visit(tree)

    def extract_lhs_signal(self, ctx):
        """
        Extracts the left-hand side signal name from an assign_stmt.
        Assumes: assign identifier = expr ;
        """
        if hasattr(ctx, "Identifier"):
            return ctx.Identifier().getText()
        raise ValueError("continuous_assign context missing net_lvalue")

    def visitCompilation_unit(self, ctx):
        # For now, just visit the first module
        return self.visit(ctx.module_declaration(0))

    def visitModule_declaration(self, ctx):
        self.signal_map = {}
        
        print("visiting module_declaration")
        result = self.visitChildren(ctx)
        #for child in ctx.children:
        #    if isinstance(child, AssignStmtCtxtClass):
        #        logic_tree = self.visit(child)
        #        lhs_signal = self.extract_lhs_signal(child)
        #        self.signal_map[lhs_signal] = logic_tree
        #        print(f"[assign] {lhs_signal} = {logic_tree}")
        print("signal_map contents:", self.signal_map)
    
        return next(iter(self.signal_map.values())) if self.signal_map else None

    def visitModule_item(self, ctx):
        return self.visitChildren(ctx)

    def visitContinuous_assign_statement(self, ctx):
        print("visitContinuousAssign_statement")
        logic_tree = self.visit(ctx.expr())
        lhs_signal = self.extract_lhs_signal(ctx)
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree
            
    def visitContinuous_assign(self, ctx):
        print("visitContinuous_assign")
        logic_tree = self.visit(ctx.expression())
        lhs_signal = self.extract_lhs_signal(ctx)
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree

    def visitAssign_statement(self, ctx):
        logic_tree = self.visit(ctx.expr())
        lhs_signal = self.extract_lhs_signal(ctx)
        self.signal_map[lhs_signal] = logic_tree
        return logic_tree

    def visitExpression(self, ctx):
        if ctx.getChildCount() == 1:
            if ctx.identifier():
                print(f"[DEBUG] visitExpression -> LogicVar: {ctx.getText()}")
                return LogicVar(ctx.getText())
            if ctx.literal():
                const = self.visitLiteral(ctx.literal())
                print(f"[DEBUG] visitExpression -> Const: {const}")
                return const

        elif ctx.getChildCount() == 2:  # Unary (e.g. ~a)
            op = ctx.getChild(0).getText()
            rhs = self.visit(ctx.getChild(1))
            print(f"[DEBUG] Unary op '{op}' on {rhs}")
            if op == '~':
                print(f"DEBUG: visitExpression() self.name: {self.name}, rhs: {rhs}")
                return LogicOp("NOT", [rhs])

        elif ctx.getChildCount() == 3:
            lhs = self.visit(ctx.getChild(0))
            op = ctx.getChild(1).getText()
            rhs = self.visit(ctx.getChild(2))
            print(f"[DEBUG] Binary '{op}': lhs={lhs}, rhs={rhs}")

            if op == '&': return LogicOp("AND", [lhs, rhs])
            if op == '|': return LogicOp("OR", [lhs, rhs])
            if op == '^': return LogicOp("XOR", [lhs, rhs])
            if op == '~^': return LogicOp("XNOR", [lhs, rhs])
            if op == '==':
                if isinstance(rhs, list):
                    print(f"[DEBUG] Expanding bitvector comparison: {lhs} == {rhs}")
                    return LogicOp("AND", [
                        LogicOp("XNOR", [LogicVar(f"{lhs.name}_{i}"), LogicConst(bit)])
                        for i, bit in enumerate(rhs)
                    ])
                else:
                    return LogicOp("XNOR", [lhs, rhs])

        elif ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(':
            print("[DEBUG] Parenthesized expression")
            return self.visit(ctx.getChild(1))  # Parenthesized

        raise NotImplementedError("Unhandled expression structure: " + ctx.getText())

    def visitLogicalNotExpr(self, ctx):
        expr = self.visit(ctx.expression())
        return LogicOp("NOT", [expr])

    def visitBitwiseNotExpr(self, ctx):
        expr = self.visit(ctx.expression())
        return LogicOp("NOT", [expr])  # or differentiate if needed

    def visitNegateExpr(self, ctx):
        expr = self.visit(ctx.expression())
        # Treat -a as NOT(a) for logic, or raise NotImplementedError if arithmetic
        return LogicOp("NOT", [expr])

    def visitAndExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return LogicOp("AND", [lhs, rhs])

    def visitOrExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return LogicOp("OR", [lhs, rhs])

    def visitXorExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return LogicOp("XOR", [lhs, rhs])

    def visitXnorExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return LogicOp("XNOR", [lhs, rhs])

    def visitEqExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        log.debug("visitEqExpr with: lhs: {%s}, rhs: {%s}", lhs, rhs)
        log.debug("rhs type: %s",  type(rhs))


        # Case 1: Bitvector comparison against a constant like 7'b0110011
        #if isinstance(rhs, LogicConst) and isinstance(lhs, LogicHole):
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
                        var = LogicVar(f"{lhs.name}_{i}")
                        xnor = LogicOp("XNOR", [var, LogicConst(bit_val)])
                        xnor_terms.append(xnor)

                    if len(xnor_terms) == 1:
                        return xnor_terms[0]
                    else:
                        # Recursively reduce with ANDs
                        from logictree.utils import balanced_tree_reduce
                        return balanced_tree_reduce("AND", xnor_terms)

                except Exception as e:
                    print(f"[ERROR] Failed to parse bitvector comparison: {rhs_text}")
                    raise e

        # Case 2: Simple variable == variable or constant
        return LogicOp("XNOR", [lhs, rhs])

    def visitParenExpr(self, ctx):
        log.info("isitParenExpr with: %s", ctx.getText())
        return self.visit(ctx.expression())

    def visitLiteral(self, ctx):
        raw = ctx.getText()
        if "'" in raw:
            # binary constatn like 7'b0110011
            bits = text.split("'")[1][1:]
            #bits = [int(b) for b in raw.split("'")[1][1:]]
            return [int(b) for b in bits]
            #return LogicConst(bits)  # for == bitvector case
        else:
            return LogicConst(int(raw))

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
                print(f"Failed to parse bitvector constant: {text} with error: {e}")
                return LogicHole(text)
        else:
            # Just a number like `1` or `0`
            return LogicConst(int(text))

    def visitIdExpr(self, ctx):
        log.info("visitIdExpr with: %s", ctx.getText())
        return LogicHole(ctx.getText())

