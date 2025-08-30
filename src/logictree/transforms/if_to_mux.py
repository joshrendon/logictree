import logging

from logictree.nodes import (
    IfStatement,
    LogicAssign,
    LogicMux,
)

log = logging.getLogger(__name__)


def if_to_mux_tree(node: IfStatement) -> LogicAssign:
    """
    Lower a simple IfStatement (2-way branch) into a mux tree.
    Assumes the body of each branch is a single LogicAssign to the same LHS.
    """
    if node.then_branch is None or node.else_branch is None:
        raise NotImplementedError("Only full if/else supported for now")

    then_stmt = (
        node.then_branch[0] if isinstance(node.then_branch, list) else node.then_branch
    )
    else_stmt = (
        node.else_branch[0] if isinstance(node.else_branch, list) else node.else_branch
    )

    if not isinstance(then_stmt, LogicAssign) or not isinstance(else_stmt, LogicAssign):
        raise TypeError(
            "if-to-mux lowering only supports LogicAssign branches right now"
        )

    if then_stmt.lhs != else_stmt.lhs:
        raise ValueError("Mismatched LHS in if/else branches")

    mux_expr = LogicMux(node.cond, then_stmt.rhs, else_stmt.rhs)
    return LogicAssign(lhs=then_stmt.lhs, rhs=mux_expr)
