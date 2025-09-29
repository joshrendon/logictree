from logictree.nodes.ops.ite import ITE
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.ops import LogicConst

def reduce_if_to_ite(stmt, default_else=None):
    """
    Recursively collapse IfStatement chains into a single ITE expression,
    *only* if all branches assign to the same LHS.

    Returns either the original stmt (if pattern doesn't match),
    or a LogicAssign(lhs, ITE(...)).
    """

    if not isinstance(stmt, IfStatement):
        return stmt

    # then must be an assign
    if not isinstance(stmt.then_branch, LogicAssign):
        return stmt

    lhs = stmt.then_branch.lhs
    then_expr = stmt.then_branch.rhs

    # else_branch may be:
    # - another IfStatement
    # - a LogicAssign
    # - None
    if stmt.else_branch is None:
        else_expr = default_else or LogicConst(0)
    elif isinstance(stmt.else_branch, LogicAssign):
        # must match LHS
        if stmt.else_branch.lhs != lhs:
            return stmt
        else_expr = stmt.else_branch.rhs
    elif isinstance(stmt.else_branch, IfStatement):
        reduced = reduce_if_to_ite(stmt.else_branch, default_else)
        if isinstance(reduced, LogicAssign) and reduced.lhs == lhs:
            else_expr = reduced.rhs
        else:
            return stmt
    else:
        return stmt

    ite_expr = ITE(
        cond=stmt.cond,
        if_true=then_expr,
        if_false=else_expr
    )

    return LogicAssign(lhs=lhs, rhs=ite_expr)
