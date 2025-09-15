# utils/formatting.py

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar


def pretty_expr(node: LogicTreeNode) -> str:
    """
    Return a human-readable expression string for a given logic node.
    Intended for codegen (e.g., Verilog ternaries) and debug formatting.
    """
    if isinstance(node, LogicConst):
        return str(node.value)
    elif isinstance(node, LogicVar):
        return node.name
    elif isinstance(node, NotOp):
        return f"!({pretty_expr(node.operand)})"
    elif isinstance(node, AndOp):
        return f"({pretty_expr(node.lhs)} & {pretty_expr(node.rhs)})"
    elif isinstance(node, OrOp):
        return f"({pretty_expr(node.lhs)} | {pretty_expr(node.rhs)})"
    elif isinstance(node, XorOp):
        return f"({pretty_expr(node.lhs)} ^ {pretty_expr(node.rhs)})"
    elif isinstance(node, NandOp):
        return f"~({pretty_expr(node.lhs)} & {pretty_expr(node.rhs)})"
    elif isinstance(node, NorOp):
        return f"~({pretty_expr(node.lhs)} | {pretty_expr(node.rhs)})"
    elif isinstance(node, XnorOp):
        return f"~({pretty_expr(node.lhs)} ^ {pretty_expr(node.rhs)})"
    elif isinstance(node, EqOp):
        return f"({pretty_expr(node.lhs)} == {pretty_expr(node.rhs)})"
    elif isinstance(node, NeqOp):
        return f"({pretty_expr(node.lhs)} != {pretty_expr(node.rhs)})"
    elif isinstance(node, EmptyBranch):
        return "/* empty */"
    else:
        return f"<UNKNOWN {type(node).__name__}>"

def pretty_assign_expr(assign: LogicAssign) -> str:
    """
    Render a LogicAssign into a compact, algebra-like string.
    """
    lhs = assign.lhs.name
    rhs = _format_node(assign.rhs)
    return f"{lhs} = {rhs}"

def _format_node(node) -> str:
    if isinstance(node, LogicVar):
        return node.name
    if isinstance(node, LogicConst):
        return str(node)
    if isinstance(node, EmptyBranch):
        return "/* empty */"
    if isinstance(node, NotOp):
        return f"!({_format_node(node.children[0])})"
    if isinstance(node, AndOp):
        return "(" + " & ".join(_format_node(c) for c in node.children) + ")"
    if isinstance(node, OrOp):
        return "(" + " | ".join(_format_node(c) for c in node.children) + ")"
    if isinstance(node, EqOp):
        lhs, rhs = node.children
        return f"({_format_node(lhs)} == {_format_node(rhs)})"
    if isinstance(node, LogicMux):
        cond = _format_node(node.selector)
        tbranch = _format_node(node.if_true)
        fbranch = _format_node(node.if_false)
        return f"({cond}) ? {tbranch} : {fbranch}"
    if isinstance(node, LogicOp):
        return f"{node.__class__.__name__}(" + ", ".join(_format_node(c) for c in node.children) + ")"
    return f"UNKNOWN<{type(node).__name__}>"
