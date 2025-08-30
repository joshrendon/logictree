import dataclasses
import logging
import re
import sys
from dataclasses import Field
from pprint import pformat
from typing import List, Tuple

from logictree.nodes import LogicMux, control, ops
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.gates import AndOp, NotOp
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


def contains_field_object(obj):
    for name, val in vars(obj).items():
        if isinstance(val, Field):
            return name, val
    return None, None


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


log.warning(
    "Parser module: %s @ %s",
    SystemVerilogSubsetParser.__module__,
    where_defined(SystemVerilogSubsetParser),
)
log.warning(
    "Visitor module: %s @ %s",
    SystemVerilogSubsetVisitor.__module__,
    where_defined(SystemVerilogSubsetVisitor),
)


class SVToLogicTreeLowerer(SystemVerilogSubsetVisitor):
    def __init__(self):
        super().__init__()
        self.module_name = None
        self.module_map = {}
        self.output_signals = set()
        self.strict_identifiers = False
        self.logger = logging.getLogger("logictree.SVToLogicTreeLowerer")
        # name -> (msb, lsb), e.g., { "s": (3, 0), "y": (1, 0) }

    def _labels_from_case_item(self, ctx) -> Tuple[List[LogicConst], bool]:

        labels: List[LogicConst] = []

        raw_text = ctx.getText()
        is_default = raw_text.strip().lower().startswith("default")

        if is_default:
            # No need to manufacture a bogus LogicConst just return
            return [], True

        # Fallback: attempt to extract constant expressions
        expr_ctxs = getattr(ctx, "constant_expression", []) or getattr(
            ctx, "expression", []
        )
        for expr_ctx in expr_ctxs:
            expr_node = self.visit(expr_ctx)
            if not isinstance(expr_node, LogicConst):
                raise ValueError(
                    f"Expected LogicConst, got {type(expr_node)} from {expr_ctx.getText()}"
                )
            labels.append(expr_node)

        return labels, False

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
            base = m.group("base").lower()
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
        name = type(tree).__name__.replace("Context", "")
        meth = getattr(self, f"visit{name}", None)
        try:
            txt = tree.getText()
        except Exception:
            txt = "<no text>"
        log.debug(
            f"[DISPATCH] {name} -> {'visit'+name if meth else 'visitChildren'} :: {txt}"
        )
        return meth(tree) if meth else self.visitChildren(tree)

    def lower(self, ast):
        assert isinstance(ast, dict) and ast.get(
            "modules"
        ), "Expected a parsed AST with modules"
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

        # identifier_ctx = ctx.module_identifier()
        module_name = ctx.module_identifier().getText()
        self.module_name = module_name
        log.debug(f"Parsing module: {module_name}")

        mod_obj = Module(name=module_name)
        self.current_module = mod_obj
        log.debug(f"type(mod_obj.signal_map): {type(mod_obj.signal_map)}")
        log.debug(f"Module: {Module}")
        log.debug(f"Module.__dataclass_fields__: {Module.__dataclass_fields__}")

        # when you create the module
        self.current_module.vector_widths = {}  # name -> (msb:int, lsb:int)

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
        # mod_obj.signal_map = self.current_module.signal_map.copy()
        mod_obj.signal_map.update(self.current_module.signal_map)

        # Output debug summaries
        log.debug("Signal map contents after visiting module:")
        for name, tree in self.current_module.signal_map.items():
            log.debug(f" {name}: {tree}")

        log.debug("Output signals detected:")
        for out in self.output_signals:
            log.debug(f"  {out}")

        self.module_map[module_name] = mod_obj
        log.debug(f"setting module_map[{module_name}] = {mod_obj}")
        log.debug("Module Dump:\n%s", pformat(mod_obj.__dict__, indent=2))
        self.current_module = None  # Clear after processing
        return mod_obj

    def visitModule_item(self, ctx):
        log.debug("visitModule_item")
        # log.debug(f"ctx.getChildren(): {ctx.getChildren()}")
        for child in ctx.getChildren():
            log.debug(
                f"Child of module_item: {type(child).__name__}, text: {child.getText()}"
            )
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
            ids = [
                t.getText() for t in ctx.getTokens(SystemVerilogSubsetParser.Identifier)
            ]
        except Exception:
            ids = []
        if not ids:
            # fallback: strip up to the ']' if any, then strip type keywords, split on commas/space
            tail = text.split("]", 1)[-1] if "]" in text else text
            tail = re.sub(r"^(logic|wire|reg|signed|unsigned)+", "", tail)
            ids = [tok for tok in re.split(r"[,\s]+", tail) if tok]

        for name in ids:
            # create/record the var
            if name not in self.current_module.signal_map:
                var = self.current_module.signal_map.get(name, LogicVar(name))
                width = 0
                if msb is not None:
                    width = abs(msb - lsb) + 1
                    # var = var.with_width(width)
                    var = LogicVar(name, width=width)
                    self.current_module.vector_widths[name] = (msb, lsb)
                else:
                    # var = var.with_width(1)
                    var = LogicVar(name, width=1)

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
                if case_node.items and case_node.items[0].body:
                    lhs = case_node.items[0].body[0].lhs
                self.current_module.signal_map[lhs] = case_node
                log.debug(
                    f"Registered logic for {lhs}:\n{pretty_print(self.current_module.signal_map[lhs])}"
                )
                log.debug("case_node: %s", pretty_print(case_node))
            return case_node

        elif ctx.blocking_assignment():
            log.debug("visitStatement blocking_assigment")
            assign_ctx = ctx.blocking_assignment()
            lhs_name = assign_ctx.variable_lvalue().getText()
            lhs = lhs_name
            rhs_expr = assign_ctx.expression()
            rhs_tree = self.visit(rhs_expr)
            assign_node = control.LogicAssign(lhs=lhs, rhs=rhs_tree)
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
        log.debug(
            f"Assigning signal_map.get() to current_module.assignments[{lhs}] = {node}"
        )
        self.current_module.assignments[lhs] = node
        log.debug(f"[statement assign] {node}")
        return node

    # def visitBlocking_assignment(self, ctx):
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
        if not isinstance(then_result, LogicAssign):
            raise TypeError(
                f"Expected LogicAssign from then-branch, got {type(then_result)}"
            )
        lhs_then = then_result.lhs
        then_tree = then_result.rhs

        if else_stmt_ctx:
            else_result = self.visit(else_stmt_ctx)
            if not isinstance(else_result, LogicAssign):
                raise TypeError(
                    f"Expected LogicAssign from else-branch, got {type(else_result)}"
                )
            lhs_else = else_result.lhs
            else_tree = else_result.rhs
        else:
            lhs_else = lhs_then
            else_tree = ops.LogicConst(0)

        if lhs_then != lhs_else:
            raise NotImplementedError("Mismatched lhs in if/else assignment")

        mux_tree = LogicMux(selector=cond_tree, if_true=then_tree, if_false=else_tree)
        # assign = control.LogicAssign(lhs_then, mux_tree.to_primitives().simplify())
        from logictree.transforms.simplify import simplify_logic_tree

        assign = LogicAssign(lhs_then, simplify_logic_tree(mux_tree.to_primitives()))

        self.current_module.signal_map[lhs_then] = mux_tree
        self.current_module.assignments[lhs_then] = assign

        return assign

    def visitExpression_list(self, ctx):
        log.debug("visitExpression_list")
        return self.visitChildren(ctx)

    def visitContinuous_assign(self, ctx):
        log.debug("!!visitContinuous_assign")
        children = list(ctx.getChildren())
        log.debug(f"num_children: {len(children)}")
        log.debug(f"children: {children}")

        try:
            # LHS
            lhs_ctx = ctx.variable_lvalue()
            lhs = lhs_ctx.getText()

            for name, val in vars(self.current_module).items():
                if isinstance(val, dataclasses.Field):
                    log.warn(f"{name} is still a Field object: {val}")

            log.debug(f"current_module: {self.current_module}")

            log.debug("Module class: %s", type(self.current_module))
            log.debug("Module.__module__: %s", type(self.current_module).__module__)
            log.debug("Module.__dict__: %s", self.current_module.__dict__)
            lhs_var = self.current_module.signal_map.get(lhs, LogicVar(lhs))

            log.debug(
                f"type(self.current_module.assignments) = {type(self.current_module.assignments)}"
            )
            log.debug(
                f"type(self.current_module.signal_map) = {type(self.current_module.signal_map)}"
            )
            # RHS is always child[3] in "assign <lhs> = <rhs> ;"
            rhs_ctx = ctx.getChild(3)
            rhs_text = rhs_ctx.getText()
            log.debug(f"lhs: {lhs}, rhs_text: {rhs_text}")

            rhs_tree = self.visit(rhs_ctx)  # must dispatch visitor!
            log.debug(f"assign LHS = {lhs}, RHS tree = {rhs_tree}")

            from logictree.utils.debug import assert_no_fields

            log.debug(f"Creating assign: {lhs_var} = {rhs_tree}")
            assign_node = LogicAssign(lhs=lhs_var, rhs=rhs_tree)

            field_name, field_val = contains_field_object(assign_node)
            if field_name:
                log.error(
                    f"assign_node.{field_name} is a dataclasses.Field: {field_val}"
                )
                raise TypeError(
                    f"assign_node contains uninitialized dataclass field '{field_name}'"
                )

            log.debug("assign_node: %s", dataclasses.asdict(assign_node))

            for attr_name, attr_val in vars(assign_node).items():
                if isinstance(attr_val, dataclasses.Field):
                    log.error(
                        f" assign_node.{attr_name} is a dataclasses.Field: {attr_val}"
                    )
                else:
                    log.debug(f" assign_node.{attr_name} = {attr_val}")

            # optional viz label
            try:
                from logictree.utils.display import pretty_inline
                from logictree.utils.overlay import set_label

                set_label(rhs_tree, f"{lhs} = {pretty_inline(rhs_tree)}")
                # rhs_tree.set_viz_label(f"{lhs} = {pretty_inline(rhs_tree)}")
            except Exception as e:
                log.debug("Could not set viz label: %s", e)

            self.current_module.assignments[lhs_var.name] = assign_node

            log.debug("Assignments collected:")
            for k, assign in self.current_module.assignments.items():
                log.debug(f"  {k} = {assign}")

            assert_no_fields(assign_node, name="assign_tree")
            return assign_node

        except AttributeError as e:
            if "'Field' object has no attribute 'get'" in str(e):
                log.error(
                    "Likely dataclass mis-initialization: caught Field object in assign_node"
                )
                raise  # or continue
            raise
        except Exception as e:
            log.warning("visitContinuous_assign failed to parse assign")
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
            log.debug(
                f"visitCase_statement: labels, is_default: {labels}, {is_default}"
            )
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
        idx = self.visit(ctx.expression(1))
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
        msb = self.visit(ctx.expression(1))
        lsb = self.visit(ctx.expression(2))

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
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))

        # Case: vector equality with constant literal
        if isinstance(lhs, LogicVar) and isinstance(rhs, LogicConst):
            width = getattr(lhs, "width", None)
            if width is None or width == 0:
                width = (
                    rhs.width
                    if hasattr(rhs, "width")
                    else (int(rhs.value).bit_length() or 1)
                )

            hi, lo = width - 1, 0
            return self._expand_vector_comparison(lhs, hi, lo, int(rhs.value), "==")

        # Case: part-select equality with constant
        if isinstance(lhs, PartSelect) and isinstance(rhs, LogicConst):
            return self._expand_vector_comparison(
                lhs.base, lhs.msb, lhs.lsb, int(rhs.value), "=="
            )

        # Fallback
        return EqOp(lhs, rhs)

    def visitNeqExpr(self, ctx):
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))

        if isinstance(rhs, LogicConst):
            if isinstance(lhs, LogicVar):
                width = getattr(lhs, "width", None)
                if width is None or width == 0:
                    width = (
                        rhs.width
                        if hasattr(rhs, "width")
                        else (int(rhs.value).bit_length() or 1)
                    )

                hi, lo = width - 1, 0
                return self._expand_vector_comparison(lhs, hi, lo, int(rhs.value), "!=")

            if isinstance(lhs, PartSelect):
                return self._expand_vector_comparison(
                    lhs.base, lhs.msb, lhs.lsb, int(rhs.value), "!="
                )

        return NeqOp(lhs, rhs)

    def _expand_vector_comparison(
        self, base, hi: int, lo: int, const_val: int, op: str
    ):
        """
        Expand (vector == const) or (vector != const) into bit-level EqOps joined by AndOps.
        """
        width = abs(hi - lo) + 1
        const_val &= (1 << width) - 1

        terms = []
        # Align bit 0 of const_val with LSB of the slice
        for i in range(width):
            bit_index = lo + i if lo <= hi else hi + i
            bit_val = (const_val >> i) & 1
            bit_node = BitSelect(base, bit_index)
            terms.append(EqOp(bit_node, LogicConst(bit_val)))

        node = terms[0]
        for t in terms[1:]:
            node = AndOp(node, t)

        if op == "==":
            return node
        elif op == "!=":
            return NotOp(node)
        else:
            raise ValueError(f"Unsupported comparison op: {op}")

    def visitParenExpr(self, ctx):
        log.info("visitParenExpr with: %s", ctx.getText())
        return self.visit(ctx.expression())

    def visitRange(self, ctx):
        log.debug("visitRange")
        hi = int(ctx.DecimalNumber(0).getText())
        lo = int(ctx.DecimalNumber(1).getText())
        width = abs(hi - lo) + 1
        return (hi, lo, width)
        # return self.visitChildren(ctx)

    def _parse_binary_literal(self, txt: str):
        # e.g. "4'b1010" or "2'B01"
        width_str, rest = txt.split("'")
        width = int(width_str)
        bits = rest[1:]  # "1010"
        if any(ch in "xzXZ" for ch in bits):
            if not getattr(self, "allow_unknown_bits", False):
                raise ValueError(f"Unknown bits in literal: {txt}")
        val = int(bits.replace("_", "").replace("x", "0").replace("z", "0"), 2)
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
        log.debug("visitConstExpr")
        text = ctx.getText()
        log.debug(f"text: {text}")

        # Binary, hex, decimal literals
        if "'" in text:  # e.g. 2'b10, 4'hF, 8'd255
            width_str, base_and_val = text.split("'")
            log.debug(f"width_str: {width_str}, base_and_val: {base_and_val}")
            width = int(width_str) if width_str else None
            base = base_and_val[0].lower()
            val_str = base_and_val[1:]
            log.debug(f"width: {width}, base: {base}, val_str: {val_str}")

            if base == "b":
                value = int(val_str, 2)
            elif base == "h":
                value = int(val_str, 16)
            elif base == "d":
                value = int(val_str, 10)
            else:
                raise ValueError(f"Unsupported literal base: {base}")

            log.debug(f"value: {value}")
            const = LogicConst(value=value, width=width, base=base)
            log.debug("Const constructed: %r (type=%s)", const, type(const.value))
            return const

        # Pure decimal (no base)
        return LogicConst(value=int(text))

    # def visitConstExpr(self, ctx):
    #    tok = ctx.getText()
    #
    #    # Handle sized literals like 4'b1001, 8'hFF, etc.
    #    if "'" in tok:
    #        width_str, tail = tok.split("'", 1)
    #        width = int(width_str)
    #        base_char = tail[0].lower()
    #        digits = tail[1:]
    #
    #        if base_char == "b":
    #            value = int(digits, 2)
    #        elif base_char == "h":
    #            value = int(digits, 16)
    #        elif base_char == "d":
    #            value = int(digits, 10)
    #        else:
    #            raise ValueError(f"Unsupported literal base: {base_char}")
    #
    #        return LogicConst(value=value, width=width, base=base_char)
    #
    #    # Unsized decimal literal (e.g. "42")
    #    else:
    #        value = int(tok, 10)
    #        return LogicConst(value=value)

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
