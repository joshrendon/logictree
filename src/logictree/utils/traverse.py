# src/logictree/utils/traverse.py

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect


def collect_logic_vars(node):
    """Yield all LogicVar nodes inside a tree."""
    if isinstance(node, LogicVar):
        yield node

    elif isinstance(node, LogicConst):
        return  # constants have no vars

    elif isinstance(node, LogicOp):
        for child in node.children:
            yield from collect_logic_vars(child)

    elif isinstance(node, BitSelect):
        yield from collect_logic_vars(node.base)
        yield from collect_logic_vars(node.index)

    elif isinstance(node, LogicMux):
        yield from collect_logic_vars(node.selector)
        yield from collect_logic_vars(node.if_true)
        yield from collect_logic_vars(node.if_false)

    elif isinstance(node, EqOp) or isinstance(node, NeqOp):
        yield from collect_logic_vars(node.lhs)
        yield from collect_logic_vars(node.rhs)

    elif isinstance(node, LogicAssign):
        yield from collect_logic_vars(node.rhs)

    elif hasattr(node, "children"):  # fallback for custom nodes
        for child in node.children:
            yield from collect_logic_vars(child)

    else:
        return  # unhandled type
