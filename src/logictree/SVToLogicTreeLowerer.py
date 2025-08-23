import logging
import re
import sys
from typing import List, Tuple

from logictree.nodes import control, ops
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module
from logictree.utils.display import pretty_print
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor

log = logging.getLogger(__name__)
AssignStmtCtxtClass = SystemVerilogSubsetParser.Continuous_assignContext
IfStmtCtxtClass = SystemVerilogSubsetParser.If_statementContext
Expression_listCtxClass = SystemVerilogSubsetParser.Expression_listContext

_BINARY_RE = re.compile(
    r"^(?P<width>\d+)\s*'\s*(?P<base>[bBoOdDhH])\s*(?P<digits>[_0-9a-fA-FxzXZ]+)$"
)
_RANGE_RE = re.compile(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]")

def _parse_sv_int_literal(txt: str) -> int:
    s = txt.strip().lower().replace("_", "")
    # plain decimal?
    if "'" not in s:
        return int(s, 10)
    size_part, base_and_digits = s.split("'", 1)
    base_char = base_and_digits[0]
    digits = base_and_digits[1:]
    base = {"b": 2, "o": 8, "d": 10, "h": 16}.get(base_char)
    if base is None:
        raise ValueError(f"Unsupported base in literal: {txt!r}")
    # normalize unknowns to 0 for label matching
    digits = digits.translate(str.maketrans({"x": "0", "z": "0", "?": "0"}))
    return int(digits, base)


def where_defined(obj):
    mod = sys.modules.get(obj.__module__)
    path = getattr(mod, "__file__", None)
    # inspect.getfile is helpful too, but can raise for some objects
    return path or f"(module {obj.__module__} has no __file__)"

log.warning("Parser module: %s @ %s",
            SystemVerilogSubsetParser.__module__,
            where_defined(SystemVerilogSubsetParser))
log.warning("Visitor module: %s @ %s",
            SystemVerilogSubsetVisitor.__module__,
            where_defined(SystemVerilogSubsetVisitor))

class SVToLogicTreeLowerer(SystemVerilogSubsetVisitor):
    def __init__(self):
        super().__init__()
        self.module_name = None
        self.module_map = {}
        self.output_signals = set()
        self.strict_identifiers = False
        self.vector_widths: dict[str, tuple[int, int]] = {}
        self.vector_ranges: dict[str, tuple[int, int]] = {}
        self.logger = logging.getLogger("logictree.SVToLogicTreeLowerer")
        # name -> (msb, lsb), e.g., { "s": (3, 0), "y": (1, 0) }

    def bit_width(self, name: str) -> int | None:
        t = self.vector_widths.get(name)
        return (abs(t[0] - t[1]) + 1) if t else None

    def _labels_from_case_item(self, ctx) -> Tuple[List[LogicConst], bool]:
    
        labels: List[LogicConst] = []
    
        raw_text = ctx.getText()
        is_default = raw_text.strip().lower().startswith("default")
    
        if is_default:
            labels.append(LogicConst("default"))
            return labels, True
    
        # Fallback: attempt to extract constant expressions
        expr_ctxs = getattr(ctx, "constant_expression", []) or getattr(ctx, "expression", [])
        for expr_ctx in expr_ctxs:
            expr_node = self.visit(expr_ctx)
            if not isinstance(expr_node, LogicConst):
                raise ValueError(f"Expected LogicConst, got {type(expr_node)} from {expr_ctx.getText()}")
            labels.append(expr_node)
    
        return labels, False
    #def _labels_from_case_item(self, ci) -> tuple[list[LogicConst], bool]:
    #    """
    #    Extracts labels from a CaseItem parse context.
    #    Returns (labels, is_default).
    #    - labels: list of LogicConst for case labels.
    #    - is_default: True if this is a default case.
    #    """
    #    # 1) Check if it's explicitly marked default (for robust grammars)
    #    if hasattr(ci, "DEFAULT") and callable(ci.DEFAULT) and ci.DEFAULT():
    #        return [], True
    #
    #    labels: list[LogicConst] = []
    #
    #    # 2) Check for case_item_label_list → case_item_label
    #    try:

    #        if hasattr(ci, "case_item_label_list") and ci.case_item_label_list():
    #            for lab in ci.case_item_label_list().case_item_label():
    #                # Instead of parsing txt:
    #                expr = lab.expression()
    #                if expr:
    #                    val = self.visit(expr)
    #                    if isinstance(val, LogicConst):
    #                        labels.append(val)
    #            if labels:
    #                return labels, False
    #        #if hasattr(ci, "case_item_label_list") and ci.case_item_label_list():
    #        #    for lab in ci.case_item_label_list().case_item_label():
    #        #        txt = lab.getText()
    #        #        try:
    #        #            bv = BitVector.parse(txt)
    #        #            labels.append(LogicConst(bv))
    #        #            continue
    #        #        except Exception:
    #        #            # Fallback: try visiting the label
    #        #            if hasattr(lab, "expression") and lab.expression():
    #        #                expr_node = self.visit(lab.expression())
    #        #                if isinstance(expr_node, LogicConst):
    #        #                    labels.append(expr_node)
    #        #    if labels:
    #        #        return labels, False
    #    except Exception:
    #        pass  # fall through to next attempt
    #
    #    # 3) Alternative form: expression_list directly on the item
    #    try:
    #        if hasattr(ci, "expression_list") and ci.expression_list():
    #            for e in ci.expression_list().expression():
    #                txt = e.getText()
    #                try:
    #                    bv = BitVector.parse(txt)
    #                    labels.append(LogicConst(bv))
    #                except Exception:
    #                    expr_node = self.visit(e)
    #                    if isinstance(expr_node, LogicConst):
    #                        labels.append(expr_node)
    #            if labels:
    #                return labels, False

    #            if hasattr(ci, "expression_list") and ci.expression_list():
    #                for lab in ci.expression_list().expression():
    #                    # Instead of parsing txt:
    #                    expr = lab.expression()
    #                    if expr:
    #                        val = self.visit(expr)
    #                        if isinstance(val, LogicConst):
    #                            labels.append(val)
    #                if labels:
    #                    return labels, False
    #    except Exception:
    #        pass
    #
    #    # 4) Final fallback: raw text parsing, check for default keyword
    #    try:
    #        raw = ci.getText()
    #        head = raw.split(":", 1)[0].strip()
    #        parts = [p.strip() for p in head.split(",") if p.strip()]
    #        if head.lower() == "default":
    #            return [LogicConst("default")], True
    #        #if len(parts) == 1 and parts[0].lower() == "default":
    #        #    return [LogicConst("default")], True
    #        #for p in parts:
    #        #    bv = BitVector.parse(p)
    #        #    labels.append(LogicConst(bv))
    #        #if labels:
    #        #    return labels, False
    #    except Exception:
    #        pass
    #
    #    # 5) No labels and not default? Treat as empty (should be unreachable)
    #    raise ValueError("Reached default fall through no labels and no default!")
    #    return ["ERROR"], False

    def _parse_const(self, txt: str):
        """
        Parse SystemVerilog-style integer constants.
        Supports: 2'b10, 8'hFF, 12'd123, plain decimals like 42.
        X/Z are rejected unless self.allow_unknown_bits is True, in which case we coerce to 0.
        Returns (value:int, width:Optional[int])
        """
        m = _BINARY_RE.match(txt)
        if m:
            width = int(m.group("width"))
            base  = m.group("base").lower()
            digits = m.group("digits").replace("_", "")
    
            if any(ch in "xXzZ" for ch in digits):
                if not getattr(self, "allow_unknown_bits", False):
                    raise ValueError(f"Unknown bits in literal: {txt}")
                # Coerce X/Z to 0 for now (documented behavior)
                trans = str.maketrans({"x": "0", "X": "0", "z": "0", "Z": "0"})
                digits = digits.translate(trans)
    
            if base == "b":
                val = int(digits, 2)
            elif base == "o":
                val = int(digits, 8)
            elif base == "d":
                val = int(digits, 10)
            elif base == "h":
                val = int(digits, 16)
            else:
                raise ValueError(f"Unsupported base in literal: {txt}")
            return val, width
    
        # plain decimal
        if txt.isdigit():
            return int(txt), None
    
        raise ValueError(f"Unsupported literal syntax: {txt}")

    def visit(self, tree):
        # E.g., AndExprContext -> visitAndExpr
        name = type(tree).__name__.replace('Context','')
        meth = getattr(self, f'visit{name}', None)
        try:
            txt = tree.getText()
        except Exception:
            txt = "<no text>"
        log.debug(f"[DISPATCH] {name} -> {'visit'+name if meth else 'visitChildren'} :: {txt}")
        return meth(tree) if meth else self.visitChildren(tree)

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
        log.debug("visiting module_declaration")

        # Clear maps at start of module
        self.signal_map = {}
        self.output_signals = set()

        #identifier_ctx = ctx.module_identifier()
        module_name  = ctx.module_identifier().getText()
        self.module_name  = module_name
        log.debug(f"Parsing module: {module_name}")

        mod_obj = Module(name=module_name)
        self.current_module = mod_obj

        # when you create the module
        self.current_module.vector_widths = {}   # name -> (msb:int, lsb:int)

        port_list_ctx = ctx.port_list()
        if port_list_ctx:
            self.visitPort_list(port_list_ctx)

        ports = list(self.output_signals)
        log.debug(f"port_list_ctx: {port_list_ctx}")
        log.debug(f"ports: {ports}")

        log.debug(f">>>pre visit: {ctx.getText()}")
        for item in ctx.module_item():
            log.debug(f"Visiting module item: {type(item).__name__}")
            self.visitModule_item(item)

        log.debug(f">>>post visit: {ctx.getText()}")

        mod_obj.ports = ports.copy()
        mod_obj.signal_map = self.current_module.signal_map.copy()


        # Output debug summaries
        log.debug("Signal map contents after visiting module:")
        for name, tree in self.current_module.signal_map.items():
            log.debug(f" {name}: {tree}")

        log.debug("Output signals detected:")
        for out in self.output_signals:
            log.debug(f"  {out}")
        
        self.module_map[module_name] = mod_obj
        log.debug(f"setting module_map[{module_name}] = {mod_obj}")
        self.current_module = None #Clear after processing
        return mod_obj



    def visitModule_item(self, ctx):
        log.debug("visitModule_item")
        #log.debug(f"ctx.getChildren(): {ctx.getChildren()}")
        for child in ctx.getChildren():
            log.debug(f"Child of module_item: {type(child).__name__}, text: {child.getText()}")
            if isinstance(child, SystemVerilogSubsetParser.Continuous_assignContext):
                log.debug("Detected Continuous_assignContext")
                return self.visitContinuous_assign(child)
        return self.visitChildren(ctx)
    
    def visitPort_list(self, ctx):
        log.debug("visitPort_list")
        for port_ctx in ctx.port():
            self.visitPort(port_ctx)

    def visitPort(self, ctx):
        # direction: input | output | inout
        direction_tok = ctx.getChild(0).getText()
        if direction_tok not in ("input", "output", "inout"):
            return
    
        text = ctx.getText()  # e.g. "inputlogic[1:0]s" or "outputlogicy"
        # parse optional packed range "[msb:lsb]"
        msb = lsb = None
        m = re.search(r"\[(\d+)\s*:\s*(\d+)\]", text)
        if m:
            msb, lsb = int(m.group(1)), int(m.group(2))
    
        # collect identifiers (prefer tokens, fall back to a regex parse)
        try:
            ids = [t.getText() for t in ctx.getTokens(SystemVerilogSubsetParser.Identifier)]
        except Exception:
            ids = []
        if not ids:
            # fallback: strip up to the ']' if any, then strip type keywords, split on commas/space
            tail = text.split(']', 1)[-1] if ']' in text else text
            tail = re.sub(r'^(logic|wire|reg|signed|unsigned)+', '', tail)
            ids = [tok for tok in re.split(r'[,\s]+', tail) if tok]
    
        for name in ids:
            # create/record the var
            if name not in self.current_module.signal_map:
                var = self.current_module.signal_map.get(name, LogicVar(name))
                width = 0
                if msb is not None:
                    width = abs(msb-lsb) + 1
                    var = var.with_width(width)
                    self.current_module.vector_widths[name] = (msb, lsb)
                else:
                    var = var.with_width(1)

                self.current_module.signal_map[name] = var
    
            # record vector width if present
            if msb is not None:
                self.current_module.vector_widths[name] = (msb, lsb)
                width_str = f"[{msb}:{lsb}]"
            else:
                width_str = "scalar"
    
            # track output ports (matches your earlier behavior of exposing only outputs)
            if direction_tok == "output" and name not in self.current_module.ports:
                self.current_module.ports.append(name)
    
            # debug like before
            self.logger.debug(f"Port {direction_tok:<6} {name:<10} width={width_str}")

    def visitData_type(self, ctx):
        return self.visitChildren(ctx)

    def visitNet_declaration(self, ctx):
        return self.visitChildren(ctx)

    def visitAlways_comb_block(self, ctx):
        log.debug("vistAlways_comb_block")
        block = ctx.statement()
        if block is not None:
            log.debug("block: %s", block.getText())
            return self.visit(block)

    def visitStatement_item(self, ctx):
        log.debug("[visitStatement_item]")
        if ctx.case_statement():
            log.debug("visitStatement_item case_statement!")
            return self.visit(ctx.case_statement())
        if ctx.if_else_if_chain():
            log.debug("visitStatement_item if_else_if_chain!")
            return self.visit(ctx.if_else_if_chain())
        if ctx.non_blocking_assignment():
            log.debug("visitStatement_item non_blocking_assignment")
            return self.visit(ctx.non_blocking_assignment())
        if ctx.blocking_assignment():
            log.debug("visitStatement_item blocking_assignment")
            return self.visit(ctx.blocking_assignment())
        # You might also want to support begin-end blocks
        if ctx.statement():
            log.debug("visitStatement_item statement()")
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
                log.debug("Located a CaseStatement node!")
                # Extract LHS from teh first case item (assumes consistemnt assignment target)
                lhs = case_node.items[0].body.lhs
                self.current_module.signal_map[lhs] = case_node
                log.debug(f"Registered logic for {lhs}:\n{pretty_print(self.current_module.signal_map[lhs])}")
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
            self.current_module.signal_map[lhs] = rhs_tree
            log.info(f"[statement assign] {assign_node}")
            return assign_node

        elif ctx.expression():
            log.debug("visitStatement expression: %s", ctx.expression().getText())
            return self.visit(ctx.expression())
        else:
            log.warning(f"Error unknown statement context: {type(ctx)}")
            return None, None

    def visitBlocking_assignment(self, ctx):
        log.debug("visitBlocking_assignment")
        lhs = ctx.variable_lvalue().getText()
        rhs_tree = self.visit(ctx.expression())
        lhs_var = self.current_module.signal_map.get(lhs, LogicVar(lhs))
        node = LogicAssign(lhs=lhs_var, rhs=rhs_tree)
        self.current_module.assignments[lhs] = node
        log.debug(f"[statement assign] {node}")
        return node

    #def visitBlocking_assignment(self, ctx):
    #    log.debug("visitBlocking_assignment")
    #    lhs = ctx.variable_lvalue().getText()
    #    rhs_tree = self.visit(ctx.expression())
    #    
    #    assign_node = control.LogicAssign(lhs=lhs, rhs=rhs_tree)
    #    self.current_module.signal_map[lhs] = rhs_tree
    #    log.debug(f"[statement assign] {assign_node}")
    #    return assign_node

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
        self.current_module.signal_map[lhs_then] = mux_tree
        return control.LogicAssign(lhs_then, mux_tree)

    def visitExpression_list(self, ctx):
        log.debug("visitExpression_list")
        return self.visitChildren(ctx)

    def visitContinuous_assign(self, ctx):
        log.debug("!!visitContinuous_assign")
        children = list(ctx.getChildren())
        log.debug(f"num_children: {len(children)}")
        log.debug(f"children: {children}")
        try:
            lhs_ctx = ctx.variable_lvalue()
            rhs_ctx = ctx.expression()
    
            lhs = lhs_ctx.getText()
            rhs_text = rhs_ctx.getText()

            log.debug(f"lhs: {lhs}")
            log.debug(f"rhs_text: {rhs_text}")
    
            # Resolve LHS var from the module's signal map
            lhs_var = self.current_module.signal_map.get(lhs, LogicVar(lhs))

            # Build the RHS tree via vistor dispatch
            rhs_tree = self.visit(rhs_ctx)
    
            log.debug(f"Creating assign: {lhs_var} = {rhs_tree}")
            assign_node = LogicAssign(lhs=lhs_var, rhs=rhs_tree)

            try:
                from logictree.utils.display import pretty_inline
                rhs_tree.set_viz_label(f"{lhs} = {pretty_inline(rhs_tree)}")
            except Exception as e:
                log.debug("Could not set viz label: %s", e)

            self.current_module.assignments[lhs] = assign_node

            log.debug("Assignments collected:")
            for k, assign in self.current_module.assignments.items():
                log.debug(f"  {k} = {assign}")

            return assign_node
        except Exception as e:
            log.warning(f"type(ctx.getText()): {type(ctx.getText()).__name__}")
            log.warning(f"Failed to parse assign: {ctx.getText()} — {e}")
            return None

    def visitCase_statement(self, ctx):
        selector_node = self.visit(ctx.expression())  # adjust if your rule name differs
        items = []
        for ci in ctx.case_item():
            # body: adjust to your rule name (statement / statement_or_null)
            body = self.visit(ci.statement())
            labels, is_default = self._labels_from_case_item(ci)
            log.debug(f"visitCase_statement: labels, is_default: {labels}, {is_default}")
            case_item = control.CaseItem(labels=labels, default=is_default, body=body)
            items.append(case_item)
        return control.CaseStatement(selector=selector_node, items=items)


    def visitExpression(self, ctx):
        log.debug("visitExpression fallback hit")
        return self.visitChildren(ctx)

    def _as_int_if_const(self, node):
        return node.value if isinstance(node, LogicConst) else node
    
    def visitBitSelectExpr(self, ctx):
        base = self.visit(ctx.expression(0))
        idx  = self.visit(ctx.expression(1))
        # accept int or small const wrappers with .value
        if not isinstance(idx, int):
            v = getattr(idx, "value", None)
            if isinstance(v, int):
                idx = v
            elif isinstance(v, str) and v.isdigit():
                idx = int(v)
            else:
                raise ValueError("Only constant bit-select index supported for now")
        return BitSelect(base, idx)
    
    def visitPartSelectExpr(self, ctx):
        # expression '[' expression ':' expression ']'
        base = self.visit(ctx.expression(0))
        msb  = self.visit(ctx.expression(1))
        lsb  = self.visit(ctx.expression(2))
    
        def _as_int(n):
            if isinstance(n, int):
                return n
            # tolerate small "const" wrappers that expose .value
            v = getattr(n, "value", None)
            if isinstance(v, int):
                return v
            if isinstance(v, str) and v.isdigit():
                return int(v)
            raise ValueError("Only constant part-select bounds supported for now")
    
        return PartSelect(base, _as_int(msb), _as_int(lsb))

    def visitConcatExpr(self, ctx):
        parts = [self.visit(e) for e in ctx.expression()]
        return Concat(parts)

    def visitLogicalNotExpr(self, ctx):
        log.debug("visitLogicalNotExpr")
        expr = self.visit(ctx.expression())
        return ops.NotOp(expr)

    def visitBitwiseNotExpr(self, ctx):
        log.debug("visitBitwiseNotExpr")
        expr = self.visit(ctx.expression())
        return ops.NotOp(expr)  # or differentiate if needed

    def visitNegateExpr(self, ctx):
        log.debug("visitNegateExpr")
        expr = self.visit(ctx.expression())
        # Treat -a as NOT(a) for logic, or raise NotImplementedError if arithmetic
        return ops.NotOp(expr)

    def visitAndExpr(self, ctx):
        log.debug("visitAndExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.AndOp(lhs, rhs)

    def visitOrExpr(self, ctx):
        log.debug("visitOrExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.OrOp(lhs, rhs)

    def visitXorExpr(self, ctx):
        log.debug("visitXorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.XorOp(lhs, rhs)

    def visitXnorExpr(self, ctx):
        log.debug("visitXnorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return ops.XnorOp(lhs, rhs)

    def visitEqExpr(self, ctx):
        kids = list(ctx.getChildren())  # <lhs> '==' <rhs>
        lhs  = self.visit(kids[0])
        rhs  = self.visit(kids[2])
    
        if self._is_logic_var(lhs) and self._is_const(rhs):
            return self._expand_eq_var_const(self._coerce_var_node(lhs), self._to_int(rhs))
        if self._is_logic_var(rhs) and self._is_const(lhs):
            return self._expand_eq_var_const(self._coerce_var_node(rhs), self._to_int(lhs))
    
        raise NotImplementedError("Equality lowering supported for <vector> == <const> only")

    def _is_logic_var(self, node):
        # If IdExpr returns the actual var node
        for v in self.current_module.signal_map.values():
            # identity or same name → treat as var
            if node is v or getattr(node, "name", None) == getattr(v, "name", None):
                return True
        # If IdExpr returns the name (str)
        return isinstance(node, str) and node in self.current_module.signal_map
    
    def _coerce_var_node(self, node):
        # ensure we hold the node object your other passes expect
        if isinstance(node, str):
            return self.current_module.signal_map[node]
        return node
    
    def _is_logic_var(self, node):
        return isinstance(node, LogicVar)
    
    def _is_const(self, node):
        if isinstance(node, int): return True
        return hasattr(node, "value") and isinstance(node.value, int)
    
    def _expand_eq_var_const(self, var_node, const_int: int):
        # Get declared range for the vector; store this during port/signal creation.
        # Expect a dict like: self.current_module.vector_ranges[name] = (msb, lsb)
        msb, lsb = self.current_module.vector_ranges[var_node.name]
        width = abs(msb - lsb) + 1
    
        # mask/align constant to declared width
        const_int &= (1 << width) - 1
    
        # Build MSB-first terms
        terms = []
        for pos in range(width):  # pos 0 = MSB
            idx = (msb - pos) if msb >= lsb else (lsb + (width - 1 - pos))
            sel = BitSelect(var_node, idx)
            bit = (const_int >> (width - 1 - pos)) & 1
            terms.append(sel if bit else ops.NotOp(sel))
    
        node = terms[0]
        for t in terms[1:]:
            node = ops.AndOp(node, t)
        return node
    
    def _to_int(self, c):
        if isinstance(c, int):
            return c
        v = getattr(c, "value", None)
        if isinstance(v, int):
            return v
        try:
            return int(c)
        except Exception:
            pass
        raise TypeError(f"Cannot convert const {c!r} to int")
    
    def _expand_eq_var_const(self, var_node, const_value):
        const_int = self._to_int(const_value)  # <-- important
    
        left, right = self.current_module.vector_widths.get(var_node.name, (None, None))
        if left is None or right is None:
            # scalar case
            return var_node if const_int else ops.NotOp(var_node)
    
        width = abs(left - right) + 1
    
        terms = []
        for pos in range(width):                 # pos 0 = MSB, pos width-1 = LSB
            idx = (left - pos) if left >= right else (left + (width - 1 - pos))
            sel = BitSelect(var_node, idx)
            bit = (const_int >> (width - 1 - pos)) & 1
            terms.append(sel if bit else ops.NotOp(sel))
    
        node = terms[0]
        for t in terms[1:]:
            node = ops.AndOp(node, t)
        return node

    def visitParenExpr(self, ctx):
        log.info("visitParenExpr with: %s", ctx.getText())
        return self.visit(ctx.expression())

    def visitRange(self, ctx):
        log.debug("visitRange")
        return self.visitChildren(ctx)

    def _parse_binary_literal(self, txt: str):
        # e.g. "4'b1010" or "2'B01"
        width_str, rest = txt.split("'")
        width = int(width_str)
        bits = rest[1:]                  # "1010"
        if any(ch in "xzXZ" for ch in bits):
            if not getattr(self, "allow_unknown_bits", False):
                raise ValueError(f"Unknown bits in literal: {txt}")
        val = int(bits.replace('_','').replace('x','0').replace('z','0'), 2)
        return width, val
    
    def visitLiteral(self, ctx):
        log.debug("visitLiteral")
        txt = ctx.getText()
        if re.match(r"^\d+'\s*[bB]", txt):
            width, val = self._parse_binary_literal(txt)
            return LogicConst(val, width=width)
        elif re.match(r"^\d+$", txt):
            return LogicConst(int(txt), width=None)
        else:
            raise ValueError(f"Unsupported literal: {txt}")

    def visitConstExpr(self, ctx):
        txt = ctx.getText().lower().replace("_", "")  # e.g., "4'b1001", "2'b10", "42"
        if "'" not in txt:
            # plain decimal
            return int(txt)
    
        # based literal: <width>'<base><digits>
        width_str, rest = txt.split("'", 1)
        base_char = rest[0]            # b, d, h, o
        digits    = rest[1:]           # e.g., "1001"
    
        base_map = {"b": 2, "d": 10, "h": 16, "o": 8}
        base = base_map.get(base_char)
        if base is None:
            raise ValueError(f"Unsupported number base: {base_char}")
    
        # Optional: capture declared width if you care about zero-extension/truncation later
        try:
            self._last_const_width = int(width_str) if width_str else None
        except ValueError:
            self._last_const_width = None
    
        # NOTE: this assumes only 0/1 (no x/z) in tests
        return int(digits, base)

    def visitIdExpr(self, ctx):
        log.debug("visitIdExpr")
        name = ctx.getText()
        if name in self.current_module.signal_map:
            log.debug(f"found {name} in current_module.signal_map!")
            log.debug(f"returning: {self.current_module.signal_map[name]}")
            return self.current_module.signal_map[name]
        if self.strict_identifiers:
            raise ValueError(f"Signal '{name}' not found in signal_map")
        log.debug("Implicit LogicVar for '%s'", name)
        return LogicVar(name)

