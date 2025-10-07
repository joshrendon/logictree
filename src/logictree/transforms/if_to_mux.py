import logging

from logictree.nodes import LogicMux
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.ifstatement import IfStatement
from logictree.utils.transforms import unwrap_branch
from logictree.nodes.control.alwaysblock import BlockStatement
from logictree.nodes.control.assign import ProceduralAssign

log = logging.getLogger(__name__)

#def unwrap_branch(branch):
#    if isinstance(branch, list) and len(branch) == 1:
#        return branch[0]
#    return branch

def unwrap_branch(branch):
    """Strip away trivial BlockStatement(ProceduralAssign) wrappers.

    If the branch is exactly a BlockStatement containing one ProceduralAssign
    to the same LHS as the outer assignment, return just the RHS.
    Otherwise return the branch as-is.
    """

    if isinstance(branch, BlockStatement):
        if (len(branch.statements) == 1
                and isinstance(branch.statements[0], ProceduralAssign)):
            return branch.statements[0].rhs
    return branch

def if_to_mux_tree(node: IfStatement) -> LogicTreeNode:
    """
    Recursively lower IfStatement to nested mux expressions.
    Expects node to be the rhs of a LogicAssign.
    """
    log.debug(f"[if_to_mux] node type: {type(node)}")
    log.debug(f"then_branch: {node.then_branch}")
    log.debug(f"else_branch: {node.else_branch}")
    if node.then_branch is None or node.else_branch is None:
        raise NotImplementedError("Only full if/else supported")

    # RECURSE
    then_expr = (
        if_to_mux_tree(node.then_branch) if isinstance(node.then_branch, IfStatement)
        else node.then_branch
    )

    else_expr = (
        if_to_mux_tree(node.else_branch) if isinstance(node.else_branch, IfStatement)
        else node.else_branch
    )

    return LogicMux(
        selector=node.cond,
        if_true=unwrap_branch(then_expr),
        if_false=unwrap_branch(else_expr)
    )
