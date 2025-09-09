import logging

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.assign import LogicAssign

from logictree.nodes import (
    LogicMux,
)

log = logging.getLogger(__name__)

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

    return LogicMux(selector=node.cond, if_true=then_expr, if_false=else_expr)
#def if_to_mux_tree(node: IfStatement) -> LogicAssign:
#    """
#    Lower a simple IfStatement (2-way branch) into a mux tree.
#    Assumes the body of each branch is a single LogicAssign to the same LHS.
#    """
#    log.debug(f"[if_to_mux] node type: {type(node)}")
#    if not isinstance(node, IfStatement):
#        raise TypeError(f"Expected IfStatement, got {type(node).__name__}")
#
#
#    if node.then_branch is None or node.else_branch is None:
#        raise NotImplementedError("Only full if/else supported for now")
#
#    log.debug(f"type(then_branch): {type(node.then_branch).__name__}")
#    log.debug(f"type(else_branch): {type(node.else_branch).__name__}")
#    then_stmt = (
#        node.then_branch[0] if isinstance(node.then_branch, list) else node.then_branch
#    )
#    else_stmt = (
#        node.else_branch[0] if isinstance(node.else_branch, list) else node.else_branch
#    )
#    log.debug(f"type(then_stmt): {type(then_stmt).__name__}")
#    log.debug(f"type(else_stmt): {type(else_stmt).__name__}")
#
#    if isinstance(then_stmt, IfStatement) or isinstance(else_stmt, IfStatement):
#        raise NotImplementedError("Nested IfStatements not supported in if_to_mux_tree() yet")
#
#    if not isinstance(then_stmt, LogicAssign) or not isinstance(else_stmt, LogicAssign):
#        raise TypeError(
#            "if-to-mux lowering only supports LogicAssign branches right now"
#        )
#
#    if then_stmt.lhs != else_stmt.lhs:
#        raise ValueError("Mismatched LHS in if/else branches")
#
#    mux_expr = LogicMux(cond=node.cond, then_branch=then_stmt.rhs, else_branch=else_stmt.rhs)
#    return LogicAssign(lhs=then_stmt.lhs, rhs=mux_expr)
