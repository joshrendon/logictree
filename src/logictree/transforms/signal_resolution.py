from logictree.nodes import ops, control, base, hole
from logictree.nodes.base import LogicTreeNode
import logging
log = logging.getLogger(__name__)

def resolve_signal_vars(tree: LogicTreeNode, signal_map: dict) -> LogicTreeNode:
    """
    Recursively replaces LogicVar nodes with their corresponding tree in signal_map.
    Returns a new tree with inlined signal definitions.
    """
    if isinstance(tree, ops.LogicVar):
        if tree.name in signal_map:
            resolved = resolve_signal_vars(signal_map[tree.name], signal_map)
            return resolved
        return tree
    elif isinstance(tree, ops.LogicOp):
        new_children = [resolve_signal_vars(child, signal_map) for child in tree.children]
        return tree.__class__(*new_children)
    else:
        return tree
__all__ = ["resolve_signal_vars"]
