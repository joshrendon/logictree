from sv_parser.ast_nodes import BinaryOp, CaseStatement, IfElse


def to_if_tree(case_stmt: CaseStatement):
    """
    Transform a CaseStatement into nested IfElse trees.
    """
    def make_eq(cond_expr, match_expr):
        return BinaryOp('==', cond_expr, match_expr)

    if not isinstance(case_stmt, CaseStatement):
        raise TypeError("Expected CaseStatement node")

    expr = case_stmt.expr
    items = case_stmt.items
    default = case_stmt.default

    def lower_items(index):
        if index >= len(items):
            if default:
                # If default exists, wrap as "else" block
                return default[0] if len(default) == 1 else default
            else:
                return None  # no match and no default

        item = items[index]
        cond = make_eq(expr, item.pattern)
        then = item.statements[0] if len(item.statements) == 1 else item.statements
        otherwise = lower_items(index + 1)

        return IfElse(cond=cond, then_branch=then, else_branch=otherwise)

    return lower_items(0)