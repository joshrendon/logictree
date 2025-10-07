import dataclasses
import logging
import re
import sys
from dataclasses import Field
from pprint import pformat
from typing import List, Tuple

from logictree.constants import EMPTY_BRANCH
from logictree.nodes import control, ops
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign, ContinuousAssign, ProceduralAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.ops import LogicConst, LogicVar, LogicOp
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp, XorOp, XnorOp
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module
from logictree.nodes.struct.signal import LogicType, DataType
from logictree.nodes.control.alwaysblock import AlwaysBlock, AlwaysKind
from logictree.nodes.struct.statement import BlockStatement
from logictree.utils.display import pretty_print
from logictree.utils.display import pretty_inline
from logictree.utils.overlay import set_label
from logictree.utils.debug import assert_no_fields
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from sympy import symbols, simplify, Piecewise
from sympy.logic.boolalg import ITE

log = logging.getLogger(__name__)
AssignStmtCtxtClass = SystemVerilogSubsetParser.Continuous_assignContext
IfStmtCtxtClass = SystemVerilogSubsetParser.If_statementContext
Expression_CtxClass = SystemVerilogSubsetParser.ExpressionContext

_BINARY_RE = re.compile(
    r"^(?P<width>\d+)\s*'\s*(?P<base>[bBoOdDhH])\s*(?P<digits>[_0-9a-fA-FxzXZ]+)$"
)
_RANGE_RE = re.compile(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]")

def unwrap_block(node):
    """Return a list of contained statements if this is a BlockStatement, else wrap it in a list."""
    if isinstance(node, BlockStatement):
        return node.statements
    return [node]

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


class SVToLogicTreeLowerer(SystemVerilogSubsetVisitor):
    def __init__(self):
        super().__init__()
        self.module_name = None
        self.module_map = {}
        #self.output_signals = set()
        self.strict_identifiers = False
        self.logger = logging.getLogger("logictree.SVToLogicTreeLowerer")
        # name -> (msb, lsb), e.g., { "s": (3, 0), "y": (1, 0) }

    def _sanity_check_signal_map(self, signal_map: dict):
        for k, v in signal_map.items():
            if not isinstance(k, str):
                raise TypeError(f"[BUG] Signal map key must be str, got {type(k).__name__}: {k!r}")
            if not isinstance(v, (LogicVar, LogicAssign, CaseStatement, IfStatement)):
                raise TypeError(f"[BUG] Signal map value must be LogicTreeNode, got {type(v).__name__}: {v!r}")

    def _labels_from_case_item(self, ctx) -> Tuple[List[LogicConst], bool]:
        is_default = ctx.DEFAULT() is not None
        if is_default:
            return [], True
    
        labels: List[LogicConst] = []
    
        expr_list_ctx = ctx.expression()
        if expr_list_ctx is not None:
            #for expr_ctx in expr_list_ctx.expression():
            for expr_ctx in expr_list_ctx:
                expr_node = self.visit(expr_ctx)
                if not isinstance(expr_node, LogicConst):
                    raise TypeError(
                        f"Expected LogicConst, got {type(expr_node)} from {expr_ctx.getText()}"
                    )
                labels.append(expr_node)
    
        log.debug("Parsed case labels: %s", [str(l) for l in labels])
        return labels, False
    #def _labels_from_case_item(self, ctx) -> Tuple[List[LogicConst], bool]:
    #    is_default = ctx.DEFAULT() is not None
    #
    #    if is_default:
    #        return [], True
    #
    #    labels = []
    #    for expr_ctx in ctx.expression_list():
    #        label = self.visit(expr_ctx)
    #        if not isinstance(label, LogicConst):
    #            raise TypeError(f"Expected LogicConst in case label, got {type(label)}")
    #        labels.append(label)
    #
    #    return labels, False

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

        # identifier_ctx = ctx.module_identifier()
        module_name = ctx.module_identifier().getText()
        self.module_name = module_name
        log.debug(f"Parsing module: {module_name}")

        mod_obj = Module(name=module_name)
        self.current_module = mod_obj
        log.debug(f"type(mod_obj.signal_map): {type(mod_obj.signal_map)}")
        log.debug(f"Module: {Module}")
        #log.debug(f"Module.__dataclass_fields__: {Module.__dataclass_fields__}")

        port_list_ctx = ctx.port_list()
        if port_list_ctx:
            self.visitPort_list(port_list_ctx)

        #ports = list(self.output_signals)
        log.debug(f"port_list_ctx: {port_list_ctx.getText()}")
        #log.debug(f"ports: {ports}")

        for item in ctx.module_item():
            log.debug(f"Visiting module item: {type(item).__name__}")
            self.visitModule_item(item)

        mod_obj.signal_map.update(self.current_module.signal_map)
        mod_obj.vector_widths.update(self.current_module.vector_widths)

        # Output debug summaries
        log.debug("Signal map contents after visiting module:")
        for name, tree in self.current_module.signal_map.items():
            log.debug(f" {name}: {tree}")

        #log.debug("Output signals detected:")
        #for out in self.output_signals:
        #    log.debug(f"  {out}")

        self.module_map[module_name] = mod_obj
        self._sanity_check_signal_map(mod_obj.signal_map)
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
                #return self.visitContinuous_assign(child)
        if ctx.net_declaration():
            return self.visit(ctx.net_declaration())
        elif ctx.continuous_assign():
            #assign = self.visit(ctx.continuous_assign())
            assign = self.visit(ctx.continuous_assign())
            self.current_module.assignments[assign.lhs.name] = assign
        elif ctx.always_construct():
            ab = self.visit(ctx.always_construct())
            if ab is not None:
                self.current_module.always_blocks.append(ab)
            return ab
        return self.visitChildren(ctx)

    def visitAlways_construct(self, ctx):
        label = None
        kind = AlwaysKind.COMB  # default
    
        if ctx.event_control():
            ec = ctx.event_control()
            # Check which alt we matched
            if isinstance(ec, SystemVerilogSubsetParser.WildcardSensitivityBareContext):
                kind = AlwaysKind.COMB
            elif isinstance(ec, SystemVerilogSubsetParser.WildcardSensitivityParenContext):
                kind = AlwaysKind.COMB
            elif isinstance(ec, SystemVerilogSubsetParser.ExplicitSensitivityContext):
                # Check for posedge/negedge inside event_expression
                if ec.event_expression().edge_identifier():
                    kind = AlwaysKind.SEQ
                else:
                    kind = AlwaysKind.COMB
        elif ctx.getText().startswith("always_comb"):
            kind = AlwaysKind.COMB
    
        # Body
        body_stmt = self.visit(ctx.statement())
        if not isinstance(body_stmt, BlockStatement):
            body = BlockStatement(statements=[body_stmt] if body_stmt else [])
        else:
            body = body_stmt
        #if isinstance(body_stmt, list):
        #    log.debug(f"Wrapped statments in BlockStatement")
        #    body = BlockStatement(statements=body_stmt)
        #else:
        #    body = BlockStatement(statements=[body_stmt])
    
        # Label from begin : myblk
        if ctx.statement().begin_end_block():
            label_ctx = ctx.statement().begin_end_block().Identifier()
            if label_ctx:
                label = label_ctx.getText()
    
        return AlwaysBlock(kind=kind, label=label, body=body)

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
            if name not in self.current_module.signal_map:
                width = abs(msb - lsb) + 1 if msb is not None else 1
                var = LogicVar(name=name, width=width)
                self.current_module.signal_map[var.name] = var
        
            if msb is not None:
                self.current_module.vector_widths[name] = (msb, lsb)
                width_str = f"[{msb}:{lsb}]"
            else:
                width_str = "scalar"
        
            if direction_tok == "output" and name not in self.current_module.ports:
                log.debug(f"capturing new output port: {name}")
                self.current_module.ports.append(name)
        
            self.logger.debug(f"Port {direction_tok:<6} {name:<10} width={width_str}")

    def visitData_type(self, ctx):
        log.debug("visitData_type()")
        if ctx.LOGIC():
            kind = DataType.LOGIC
        elif ctx.REG():
            kind = DataType.REG
        elif ctx.WIRE():
            kind = DataType.WIRE
        else:
            kind = DataType.LOGIC  # fallback (shouldn't happen)
        width = 1
        if ctx.range():
            msb = int(ctx.range().constant_expression(0).getText())
            lsb = int(ctx.range().constant_expression(1).getText())
            width = abs(msb - lsb) + 1
        return LogicType(kind=kind, width=width)

    def visitNet_declaration(self, ctx):
        log.debug("visitNet_declaration()")

        if ctx.data_type():
            dtype = self.visit(ctx.data_type())
        else:
            # Default fallback
            dtype = LogicType(kind=DataType.LOGIC, width=1)

        # Get identifiers
        for ident_ctx in ctx.list_of_net_identifiers().identifier():
            name = ident_ctx.getText()
            self.current_module.signal_map[name] = dtype
            self.logger.info(f"Signal {name} has no explicit type; defaulting to logic [0:0]" if not ctx.data_type() else f"Declared {dtype} {name}")
        return None

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
        if ctx.nonblocking_assignment():
            log.debug("visitStatement_item nonblocking_assignment")
            return self.visit(ctx.nonblocking_assignment())
        if ctx.blocking_assignment():
            log.debug("visitStatement_item blocking_assignment")
            return self.visit(ctx.blocking_assignment())
        # You might also want to support begin-end blocks
        if ctx.statement():
            log.debug("visitStatement_item statement()")
            return self.visit(ctx.statement())
        return None

    def visitStatement(self, ctx):
        log.info(f"visitStatement - ctx: {ctx.getText()}")
        if ctx.begin_end_block():
            log.info("visitStatement begin_end_block")
            block = ctx.begin_end_block()
            stmts = []
            for child in block.statement():
                stmt_node = self.visit(child)
                
                if isinstance(stmt_node, BlockStatement):
                    log.debug(f"stmt_node is BlockStatement")
                    # flaten nested block
                    stmts.extend(stmt_node.statements)
                elif stmt_node is not None:
                    log.debug(f"stmt_node is not None")
                    log.debug(f"stmt_node.type: {type(stmt_node).__name__}")
                    stmts.append(stmt_node)
            log.debug(f"Wrapped statments in BlockStatement")
            return BlockStatement(statements=stmts)

        elif ctx.if_statement():
            log.info("visitStatement if_statement")
            return self.visit(ctx.if_statement())

        elif ctx.case_statement():
            log.info("visitStatement case_statement")
            case_node = self.visit(ctx.case_statement())
            if isinstance(case_node, CaseStatement) and case_node.items:
                #body0 = case_node.items[0].body              # always BlockStatement now
                body0 = self._as_block(case_node.items[0].body) #normalize
                #if isinstance(body0, list):
                #    log.warning("body0 is a list")
                #    log.debug(f"body0: {body0}")
                assert(isinstance(body0, BlockStatement)), f"{type(body0).__name__}"
                if body0.statements and hasattr(body0.statements[0], "lhs"):
                    lhs = body0.statements[0].lhs
                    # record the assignment target for the module
                    # Option A: store the CaseStatement itself (later passes will lower it)
                    assign = LogicAssign(lhs=LogicVar(lhs.name), rhs=case_node, blocking=None)
                    self.current_module.assignments[lhs.name] = assign
                else:
                    log.warning("First case arm did not begin with an assignment")
            return case_node
        #elif ctx.case_statement():
        #    log.debug("visitStatement case_statement")
        #    case_node = self.visit(ctx.case_statement())
        #    if isinstance(case_node, CaseStatement):
        #        log.debug("Located a CaseStatement node!")
        #        # Extract LHS from the first case item (assumes consistemnt assignment target)
        #        if case_node.items and case_node.items[0].body:
        #            #lhs = case_node.items[0].body[0].lhs
        #            #body = unwrap_block(case_node.items[0].body)
        #            body_node = case_node.items[0].body
        #            log.info(f"Located body_node: {body_node}")
        #            log.info(f"Located type(body_node): {type(body_node).__name__}")
        #            if isinstance(body_node, BlockStatement):
        #                if body_node.statements and hasattr(body_node.statements[0], "lhs"):
        #                    lhs = body_node.statements[0].lhs
        #                    log.info(f"lhs.name: {lhs.name}")
        #                    self.current_module.signal_map[lhs.name] = case_node

        #                    if lhs is not None:
        #                        assign = LogicAssign(lhs=LogicVar(lhs.name), rhs=case_node, blocking=None)
        #                        #self.current_module.assignments[lhs.name] = assign
        #                        log.debug("case_node: %s", pretty_print(case_node))
        #                        log.debug("assign: %s", pretty_print(assign))
        #                        return assign 
        #                else:
        #                    log.warning("CaseStatement BlockStatemnt had no LogicAssign in the body")
        #                    return case_node
        #            elif hasattr(body_node, "lhs"):
        #                lhs = body_node.lhs
        #                log.info(f"lhs.name: {lhs.name}")
        #                self.current_module.signal_map[lhs.name] = case_node
        #                if lhs is not None:
        #                    assign = LogicAssign(lhs=LogicVar(lhs.name), rhs=case_node, blocking=None)
        #                    #self.current_module.assignments[lhs.name] = assign
        #                    log.debug(f"lhs.name: {lhs.name}")
        #                    log.debug("case_node: %s", pretty_print(case_node))
        #                    log.debug("assign: %s", pretty_print(assign))
        #                    return assign 
        #            else:
        #                log.warning("CaseStatement body has no LogicAssign lhs")
        #                return case_node


        elif ctx.blocking_assignment():
            log.info("visitStatement blocking_assigment")
            #assign_ctx = ctx.blocking_assignment()
            #lhs_name = assign_ctx.variable_lvalue().getText()
            #lhs = lhs_name
            #rhs_expr = assign_ctx.expression()
            #rhs_tree = self.visit(rhs_expr)
            #assign_node = LogicAssign(lhs=lhs, rhs=rhs_tree, blocking=True)
            #log.debug(f"assigning LogicAssign(lhs={lhs}, rhs={rhs_tree})")
            #log.debug(f"!! rhs_tree.name: {rhs_tree.name}")
            #self.current_module.signal_map[rhs_tree.name] = rhs_tree
            #log.debug(f"[statement assign] {assign_node}")
            #return assign_node
            assign_ctx = ctx.blocking_assignment()
            lhs_name = assign_ctx.variable_lvalue().getText()
            lhs = LogicVar(lhs_name)  # wrap as LogicVar for consistency
            rhs_tree = self.visit(assign_ctx.expression())

            #if lhs in self.current_module.signal_map and self.current_module.signal_map[lhs] is not None:
            #    # Already has an expression, so wrap it into an ITE
            #    old_expr = self.current_module.signal_map[lhs].expr
            #    new_expr = ITE(cond, rhs, old_expr)  # or Piecewise if numeric
            #    log.debug(f"found old lhs in signal_map: lhs: {lhs}")
            #    log.debug(f"old_expr: {old_expr}")
            #    log.debug(f"assigning {new_expr}")
            #    self.current_module.signal_map[lhs] = new_expr
            #else:
            # First Assignment
            assign_node = ProceduralAssign(lhs=lhs, rhs=rhs_tree, blocking=True)
            log.debug(f"assigning {assign_node}")

            # Put the assignment in the module's assignments
            ##self.current_module.assignments[lhs_name] = assign_node

            # Keep signal_map entry as the LHS variable, not the RHS op
            self.current_module.signal_map[lhs_name] = lhs

            return assign_node

        elif ctx.nonblocking_assignment():
            log.info("visitStatement nonblocking_assigment")
            #self.visit(ctx.nonblocking_assignment())
            return self.visitNonblocking_assignment(ctx.nonblocking_assignment())

        elif ctx.expression():
            log.info("visitStatement expression: %s", ctx.expression().getText())
            return self.visit(ctx.expression())
        else:
            log.warning(f"Error unknown statement context: {type(ctx)}")
            return None, None

    def visitBlocking_assignment(self, ctx):
        log.debug("visitBlocking_assignment")
        lhs = ctx.variable_lvalue().getText()
        rhs_tree = self.visit(ctx.expression())
        lhs_var = self.current_module.get_signal(lhs)
        node = ProceduralAssign(lhs=lhs_var, rhs=rhs_tree, blocking=True)
        log.debug(f"Assigning signal_map.get() to current_module.assignments[{lhs}] = {node}")
        log.debug(f"{node.pretty_inline()}")
        log.debug(f"node.blocking: {node.blocking}")
        #self.current_module.assignments[lhs_var.name] = node
        log.debug(f"[statement assign] {node}")
        return node

    def visitNonblocking_assignment(self, ctx):
        log.debug("visitNonblocking_assignment")
        lhs = ctx.variable_lvalue().getText()
        rhs_tree = self.visit(ctx.expression())
        lhs_var = self.current_module.get_signal(lhs)
        node = ProceduralAssign(lhs=lhs_var, rhs=rhs_tree, blocking=False)
        log.debug(f"Assigning signal_map.get() to current_module.assignments[{lhs}] = {node}")
        log.debug(f"{node.pretty_inline()}")
        log.debug(f"node.blocking: {node.blocking}")
        #self.current_module.assignments[lhs_var.name] = node
        log.debug(f"[statement assign] {node}")
        return node

    def visitIf_statement(self, ctx):
        log.debug("DEBUG: visitIf_statement()")
        cond_tree = self.visit(ctx.expression())

        then_stmt_ctx = ctx.statement(0)
        else_stmt_ctx = ctx.statement(1) if ctx.ELSE() else None

        log.debug(f"then_stmt_ctx: {then_stmt_ctx.getText()}")
        
        log.debug(f"else_stmt_ctx: {else_stmt_ctx.getText()}") if else_stmt_ctx is not None else ""

        then_result = self.visit(then_stmt_ctx)
        if not isinstance(then_result, (LogicAssign, ProceduralAssign, ContinuousAssign)):
            log.warning("then_branch is not LogicAssign, wrapping in fallback")

        if not isinstance(then_result, LogicAssign):
            raise TypeError(
                f"Expected LogicAssign from then-branch, got {type(then_result)}"
            )
        lhs_then = then_result.lhs
        then_tree = then_result.rhs
        assert not isinstance(lhs_then, str)

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
            else_tree = LogicConst(0)

        if lhs_then != lhs_else:
            raise NotImplementedError("Mismatched lhs in if/else assignment")
        # Create and return a proper IfStatement node
        if_stmt = IfStatement(
            cond=cond_tree,
            then_branch=then_tree,
            else_branch=else_tree,
        )
    
        assign = LogicAssign(lhs=lhs_then, rhs=if_stmt, blocking=None)

        # Add a temporary assertion right before return in visitIf_statement
        assert isinstance(assign.rhs, IfStatement), f"Got: {type(assign.rhs)}"

        self.current_module.signal_map[lhs_then.name] = if_stmt
        #self.current_module.assignments[lhs_then.name] = assign

        return assign

    def visitExpression_list(self, ctx):
        log.debug("visitExpression_list")
        return self.visitChildren(ctx)

    def probe_tree(self, node, depth=0):
        pad = "  " * depth
        log.debug(f"{pad}{type(node).__name__}: {node}")
        for attr in ("left", "right", "rhs", "value"):
            if hasattr(node, attr):
                child = getattr(node, attr)
                log.debug(f"{pad}  .{attr} -> {child}")
                if isinstance(child, (LogicOp, LogicVar, LogicConst)):  # your node base classes
                    self.probe_tree(child, depth + 1)

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
            #lhs_var = self.current_module.signal_map.get(lhs, LogicVar(lhs))
            lhs_var = self.current_module.get_signal(lhs)

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
            log.debug(f"RHS tree = {repr(rhs_tree)}")
            self.probe_tree(rhs_tree)
            #rhs_right = rhs_tree.right
            #if hasattr(rhs_right, "rhs"):
            #    log.debug(f"RHS.right probe: {rhs_tree.right}")
            #    log.debug(f"right.rhs: {rhs_right.rhs}")
            #    log.debug(f"right.rhs.value: {rhs_right.rhs.value}")
            #    log.debug(f"right.rhs: type {type(rhs_right.rhs).__name__}")
            #else:
            #    log.debug(f"rhs_right is a leaf: {rhs_tree}")

            log.debug(f"Creating assign: {lhs_var} = {rhs_tree.label()}")
            assign_node = ContinuousAssign(lhs=lhs_var, rhs=rhs_tree, blocking=None)

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
                    log.info(f" assign_node.{attr_name} = {attr_val}")

            # optional viz label
            try:
                set_label(rhs_tree, f"{lhs} = {pretty_inline(rhs_tree)}")
                # rhs_tree.set_viz_label(f"{lhs} = {pretty_inline(rhs_tree)}")
            except Exception as e:
                log.debug("Could not set viz label: %s", e)

            self.current_module.assignments[lhs_var.name] = assign_node

            log.debug("Assignments collected:")
            for k, assign in self.current_module.assignments.items():
                log.debug(f"  {k} -> {pretty_print(assign)}")

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
            import traceback
            log.warning("Full exception:\n%s", traceback.format_exc())
            # Extra type diagnostics (try to dump LHS and RHS subexpressions if possible)
            try:
                lhs = ctx.variable_lvalue().getText()
                rhs = ctx.expression().getText()
                logging.warning("LHS: %s", lhs)
                logging.warning("RHS: %s", rhs)
            except Exception as e2:
                logging.warning("Couldn't extract LHS/RHS: %s", str(e2))
        
            raise  # re-raise so your test still fails

    def _as_block(self, node):
        # Normalize anything (stmt | BlockStatement | list[stmt|BlockStatement]) to BlockStatement
        if isinstance(node, BlockStatement):
            return node
        if isinstance(node, list):
            flat = []
            for s in node:
                if isinstance(s, BlockStatement):
                    flat.extend(s.statements)
                else:
                    flat.append(s)
            return BlockStatement(statements=flat)
        return BlockStatement(statements=[node])

    #def _as_block(self, node):
    #    """Normalize any visited statement into a BlockStatement."""
    #    if node is None:
    #        return BlockStatement(statements=[])
    #    if isinstance(node, BlockStatement):
    #        return node
    #    return BlockStatement(statements=[node])
    
    def visitCase_item(self, ctx):
        log.debug("visitCase_item")
        if ctx.DEFAULT():
            labels = ["default"]
        else:
            labels = [self.visit(e) for e in ctx.expression()]
        body = self.visit(ctx.statement())
        
        body = self._as_block(body)
        return CaseItem(labels=labels, body=body)

    def visitCase_statement(self, ctx):
        log.debug("visitCase_statement")
        selector = self.visit(ctx.expression())
        items = [self.visit(item) for item in ctx.case_item()]
        return CaseStatement(selector=selector, items=items)
    #def visitCase_statement(self, ctx):
    #    log.debug("visitCase_statement")
    #    unique = ctx.UNIQUE() is not None
    #    selector_node = self.visit(ctx.expression())
    #    items = []
    #
    #    for ci in ctx.case_item():
    #        labels, is_default = self._labels_from_case_item(ci)
    #
    #        # Exactly ONE statement (or null) per case item in this grammar
    #        stmt_ctx = ci.statement()
    #        stmt_node = self.visit(stmt_ctx)           # visit once
    #        body = self._as_block(stmt_node)           # normalize to BlockStatement
    #
    #        # If default is empty, make it explicit
    #        if is_default and not body.statements:
    #            body.statements.append(EMPTY_BRANCH)
    #
    #        items.append(CaseItem(labels=labels, default=is_default, body=body))
    #
    #    return CaseStatement(selector=selector_node, items=items, unique=unique)
    #def visitCase_statement(self, ctx):
    #    log.debug("visitCase_statement")
    #    unique = ctx.UNIQUE() is not None
    #    selector_node = self.visit(ctx.expression())
    #    items = []
    #
    #    for ci in ctx.case_item():
    #        labels, is_default = self._labels_from_case_item(ci)
    #
    #        # Normalize to a list of statement contexts (single or many)
    #        stmt_ctxs = ci.statement()
    #        if stmt_ctxs is None:
    #            stmt_ctxs = []
    #        elif not isinstance(stmt_ctxs, (list, tuple)):
    #            stmt_ctxs = [stmt_ctxs]
    #
    #        stmts = []
    #        for stmt_ctx in stmt_ctxs:
    #            node = self.visit(stmt_ctx)
    #            if node is None:
    #                continue
    #            if isinstance(node, BlockStatement):
    #                # flatten nested begin/end
    #                stmts.extend(node.statements)
    #                log.debug(f"Flattened BlockStatement -> {len(node.statements)} stmts")
    #            else:
    #                stmts.append(node)
    #                log.debug(f"Added stmt_node: {type(node).__name__}")
    #
    #        # Empty default branch gets an explicit sentinel
    #        if is_default and not stmts:
    #            log.debug("Inserting EMPTY_BRANCH into default case branch")
    #            stmts.append(EMPTY_BRANCH)
    #
    #        body = BlockStatement(statements=stmts)
    #        log.debug(f"Final case item body has {len(stmts)} stmts")
    #
    #        items.append(CaseItem(labels=labels, default=is_default, body=body))
    #
    #    return CaseStatement(selector=selector_node, items=items, unique=unique)
    #def visitCase_statement(self, ctx):
    #    log.debug("visitCase_statement")
    #    unique = ctx.UNIQUE() is not None
    #    selector_node = self.visit(ctx.expression())
    #    items = []
    #    for ci in ctx.case_item():
    #        labels, is_default = self._labels_from_case_item(ci)
    #        #stmt_node = self.visit(ci.statement())
    #        #body = self.visit(ci.statement())
    #        stmt_ctxs = ci.statement()
    #        if stmt_ctxs is None:
    #            stmt_ctxs = []
    #        elif not isinstance(stmt_ctxs, (list, tuple)):
    #            stmt_ctxs = [stmt_ctxs]

    #        stmts = []
    #        for stmt_ctx in stmt_ctxs:
    #            stmt_node = self.visit(stmt_ctx)
    #            if stmt_node is None:
    #                continue
    #            if isinstance(stmt_node, BlockStatement):
    #                #body = stmt_node
    #                stmts.extend(stmt_node.statements)
    #                log.debug(f"found BlockStatement stmt_node stmts: {stmts}")
    #                log.debug(f"Flattened BlockStatement -> {len(stmt_node.statements)} stmts")
    #            elif stmt_node is not None:
    #                #body = BlockStatement([stmt_node])
    #                stmts.append(stmt_node)
    #                log.debug(f"Added stmt_node: {type(stmt_node).__name__}")

    #        # If default branch is empty/null, use EMPTY_BRANCH node
    #        if is_default and not stmts:
    #            log.debug("Inserting EMPTY_BRANCH into default case branch")
    #            #body = BlockStatement([EMPTY_BRANCH])
    #            stmts.append(EMPTY_BRANCH)
    #            log.debug(f"stmts: {stmts}")

    #        body = BlockStatement(statements=stmts)
    #        log.debug(f"stmts: {stmts}")
    #        log.debug(f"Final case item body has {len(stmts)} stmts")
    #
    #        case_item = CaseItem(labels=labels, default=is_default, body=body)
    #        items.append(case_item)
    #
    #    return CaseStatement(selector=selector_node, items=items, unique=unique)

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

        return PartSelect(base, _as_int(msb), _as_int(lsb))._normalize_self()
        #return PartSelect(base, msb, lsb)._normalize_self()

    def visitConcatExpr(self, ctx):
        parts = [self.visit(e) for e in ctx.expression()]
        return Concat(parts)

    def visitLogicalNotExpr(self, ctx):
        log.debug("visitLogicalNotExpr")
        expr = self.visit(ctx.expression())
        return NotOp(expr)

    def visitBitwiseNotExpr(self, ctx):
        log.debug("visitBitwiseNotExpr")
        expr = self.visit(ctx.expression())
        return NotOp(expr)  # or differentiate if needed

    def visitNegateExpr(self, ctx):
        log.debug("visitNegateExpr")
        expr = self.visit(ctx.expression())
        # Treat -a as NOT(a) for logic, or raise NotImplementedError if arithmetic
        return NotOp(expr)

    def visitAndExpr(self, ctx):
        log.debug("visitAndExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return AndOp(lhs, rhs)

    def visitOrExpr(self, ctx):
        log.debug("visitOrExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return OrOp(lhs, rhs)

    def visitXorExpr(self, ctx):
        log.debug("visitXorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return XorOp(lhs, rhs)

    def visitXnorExpr(self, ctx):
        log.debug("visitXnorExpr")
        lhs = self.visit(ctx.expression(0))
        rhs = self.visit(ctx.expression(1))
        return XnorOp(lhs, rhs)

    def visitEqExpr(self, ctx):
        log.debug("vsitEqExpr")
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
        log.debug("vsitNeqExpr")
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

    def _expand_vector_comparison(self, base, hi: int, lo: int, const_val: int, op: str):
        """
        Expand (vector == const) or (vector != const) into bit-level EqOps joined by AndOps.
        """

        hi_val = hi.value if isinstance(hi, LogicConst) else hi
        lo_val = lo.value if isinstance(lo, LogicConst) else lo
        width = abs(hi_val - lo_val) + 1
        #width = abs(hi - lo) + 1
        const_val &= (1 << width) - 1
    
        lo = int(lo) if isinstance(lo, LogicConst) else lo
        hi = int(hi) if isinstance(hi, LogicConst) else hi
        indices = range(lo, hi + 1) if lo <= hi else range(lo, hi - 1, -1)
    
        terms = []
        for offset, bit_index in enumerate(indices):
            bit_val = (const_val >> offset) & 1
            bit_node = BitSelect(base, bit_index)  # FIX: use int index
            terms.append(EqOp(bit_node, LogicConst(bit_val)))
    
        node = terms[0]
        for t in terms[1:]:
            node = AndOp(node, t)
        if op == "==":
            return node
        elif op == "!=":
            neq_terms = []
            for offset, bit_index in enumerate(indices):
                bit_val = (const_val >> offset) & 1
                bit_node = BitSelect(base, bit_index)
                neq_terms.append(NeqOp(bit_node, LogicConst(bit_val)))
    
            node = neq_terms[0]
            for t in neq_terms[1:]:
                node = OrOp(node, t)
            return node
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
            return LogicConst(value=val, width=width)
        elif re.match(r"^\d+$", txt):
            return LogicConst(value=int(txt), width=None)
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
            log.debug(f"text: {text}")
            const = LogicConst.from_sv_literal(text)
            #const = LogicConst(value=value, width=width, base=base)
            log.debug("Const constructed: %r type(const.value): (type=%s)", const, type(const.value))
            log.debug("Const: %r", const)
            return const

        # Pure decimal (no base)
        #return LogicConst(value=int(text))
        return LogicConst.from_sv_literal(text)

    def visitIdExpr(self, ctx):
        log.debug("visitIdExpr")
        name = ctx.getText()
        log.debug(f"signal_map.keys(): {self.current_module.signal_map.keys()}")
        if name in self.current_module.signal_map:
            sig = self.current_module.get_signal(name)
            log.debug(f"found {name} in current_module.signal_map!")
            #log.debug(f"returning: {self.current_module.get_signal(name)}")
            log.debug(f"returning sig: {sig}")
            assert sig == self.current_module.signal_map[name]
            return self.current_module.signal_map[name]
        if self.strict_identifiers:
            raise ValueError(f"Signal '{name}' not found in signal_map")
        log.debug("Implicit LogicVar for '%s'", name)
        return LogicVar(name=name)
