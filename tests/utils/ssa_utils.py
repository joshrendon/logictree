from logictree.nodes.control.assign import ProceduralAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.ite import ITEOp

def lower_procedural_assigns_to_signal_map(module):
    """
    Collects sequential procedural assignments from always blocks
    and folds them into SSA form with nested ITEs.
    Updates module.signal_map in place.
    """
    for ab in module.always_blocks:
        assigns_by_lhs = {}

        for stmt in ab.body.statements:
            if isinstance(stmt, ProceduralAssign):
                assigns_by_lhs.setdefault(stmt.lhs.name, []).append(stmt)
            elif isinstance(stmt, IfStatement):
                # simplify: only handle single assign in branch for now
                if isinstance(stmt.then_branch, ProceduralAssign):
                    assigns_by_lhs.setdefault(stmt.then_branch.lhs.name, []).append(stmt)

        # build nested ITEs in SSA order
        for lhs, stmts in assigns_by_lhs.items():
            expr = None
            for stmt in stmts:
                if isinstance(stmt, ProceduralAssign):
                    if expr is None:
                        expr = stmt.rhs
                    else:
                        # unconditional assign overwrites everything before
                        expr = stmt.rhs
                elif isinstance(stmt, IfStatement):
                    inner = stmt.then_branch.rhs
                    if expr is None:
                        expr = ITEOp(stmt.cond, inner, None)  # default filled later
                    else:
                        expr = ITEOp(stmt.cond, inner, expr)

            # fill default if any leftover
            if isinstance(expr, ITEOp) and expr.if_false is None:
                expr.if_false = 0  # or LogicConst(0) if you want strict typing

            module.signal_map[lhs] = expr
