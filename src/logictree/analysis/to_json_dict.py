from functools import singledispatch

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.arith import AddOp, ArithOp, SubOp
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module
from logictree.nodes.struct.statement import BlockStatement


@singledispatch
def to_json_dict(node: LogicTreeNode) -> dict:
    raise NotImplementedError(f"No to_json_dict for {type(node)}")

@to_json_dict.register
def _(node: ArithOp) -> dict:
    return {"type": node.__class__.__name__}
@to_json_dict.register
def _(node: AddOp) -> dict:
    return {"type": node.__class__.__name__}
def _(node: SubOp) -> dict:
    return {"type": node.__class__.__name__}

# --- Leaves ---
@to_json_dict.register
def _(node: LogicVar) -> dict:
    return {"type": "LogicVar", "label": node.name, "operands": []}

@to_json_dict.register
def _(node: LogicConst) -> dict:
    return {"type": "LogicConst", "label": str(node.value), "operands": []}

@to_json_dict.register(EmptyBranch)
@to_json_dict.register(LogicHole)
def _(node) -> dict:
    return {"type": type(node).__name__, "label": node.label(), "operands": []}


# --- Generic op helper ---
def _op_dict(node, label=None):
    return {
        "type": type(node).__name__,
        "label": label or node.label(),
        "operands": [to_json_dict(c) for c in node.operands],
    }


# --- Ops ---
@to_json_dict.register(NotOp)
@to_json_dict.register(AndOp)
@to_json_dict.register(OrOp)
@to_json_dict.register(XorOp)
@to_json_dict.register(XnorOp)
@to_json_dict.register(NandOp)
@to_json_dict.register(NorOp)
@to_json_dict.register(EqOp)
@to_json_dict.register(NeqOp)
@to_json_dict.register(ITEOp)
@to_json_dict.register(LogicMux)
@to_json_dict.register(BitSelect)
@to_json_dict.register(PartSelect)
@to_json_dict.register(Concat)
def _(node) -> dict:
    return _op_dict(node)


# --- Control ---
@to_json_dict.register
def _(node: LogicAssign) -> dict:
    return {
        "type": "LogicAssign",
        "label": node.label(),
        "operands": [to_json_dict(node.rhs)],
    }

@to_json_dict.register
def _(node: IfStatement) -> dict:
    return {
        "type": "IfStatement",
        "label": node.label(),
        "then": to_json_dict(node.then_branch),
        "else": to_json_dict(node.else_branch) if node.else_branch else None,
    }

@to_json_dict.register
def _(node: CaseItem) -> dict:
    return {
        "type": "CaseItem",
        "label": str(node.label()),
        "operands": [to_json_dict(node.statement)],
    }

@to_json_dict.register
def _(node: CaseStatement) -> dict:
    return {
        "type": "CaseStatement",
        "label": node.label(),
        "operands": [to_json_dict(ci) for ci in node.case_items],
    }

@to_json_dict.register
def _(node: BlockStatement) -> dict:
    return {
        "type": "BlockStatement",
        "operands": [to_json_dict(s) for s in node.statements],
    }

# --- Module ---
@to_json_dict.register
def _(node: Module) -> dict:
    return {
        "type": "Module",
        "name": node.name,
        "assignments": [to_json_dict(a) for a in node.assignments],
    }
