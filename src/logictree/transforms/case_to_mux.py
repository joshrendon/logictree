import logging

from logictree.nodes import LogicMux
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.alwaysblock import BlockStatement
from logictree.nodes.control.assign import LogicAssign, ProceduralAssign
from logictree.nodes.control.case import CaseStatement
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.ops import LogicConst
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.if_to_mux import if_to_mux_tree

log = logging.getLogger(__name__)


def _rhs_of(node: LogicTreeNode) -> LogicTreeNode:
    """
    Extract an expression node (LogicTreeNode) from a statement-like body.
    Handles BlockStatement, Assign, EmptyBranch, and raw expressions.
    """

    # 0) Handle lists of statements (take the first element)
    if isinstance(node, list):
        if len(node) == 1:
            return _rhs_of(node[0])
        raise TypeError(f"_rhs_of() got list of len {len(node)}: {node}")

    # 1) Empty/default branch -> 0
    if isinstance(node, EmptyBranch):
        return LogicConst(0)

    # 2) BlockStatement with one assignment
    if isinstance(node, BlockStatement):
        if len(node.statements) == 1:
            stmt = node.statements[0]
            if isinstance(stmt, (LogicAssign, ProceduralAssign)):
                return stmt.rhs
        raise TypeError(f"Unsupported BlockStatement in _rhs_of: {node}")

    # 3) Direct assignment
    if isinstance(node, (LogicAssign, ProceduralAssign)):
        return node.rhs

    # 4) Already expression
    if isinstance(node, LogicTreeNode):
        return node

    raise TypeError(f"Cannot extract RHS from {type(node)}: {node}")

def case_to_mux_tree(tree):
    if not isinstance(tree, CaseStatement):
        return None

    # If a canonical 2-way, 1-bit selector mux chain is found, emit a canonical mux
    items = list(tree.items)
    if len(items) == 2:
        labels0 = getattr(items[0], "labels", [])
        labels1 = getattr(items[1], "labels", [])
        if (len(labels0) == 1 and isinstance(labels0[0], LogicConst) and labels0[0].as_int() in (0,1) and
            len(labels1) == 1 and isinstance(labels1[0], LogicConst) and labels1[0].as_int() in (0,1)):
            # sort items so we know which is 0 and which is 1
            zero_item = items[0] if labels0[0].as_int() == 0 else items[1]
            one_item  = items[0] if labels0[0].as_int() == 1 else items[1]
            a = _rhs_of(zero_item.body)
            b = _rhs_of(one_item.body)
            return LogicMux(tree.selector, b, a)

    # fallback to general lowering
    if_tree  = case_to_if_tree(tree)
    mux_tree = if_to_mux_tree(if_tree)
    return mux_tree
#def case_to_mux_tree(tree: LogicTreeNode):
#    if isinstance(tree, CaseStatement):
#        if_tree  = case_to_if_tree(tree)
#        mux_tree = if_to_mux_tree(if_tree)
#        return mux_tree
