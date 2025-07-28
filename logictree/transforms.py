from logictree.nodes import CaseStatement, LogicNode, LogicOp, LogicConst, LogicVar, LogicAssign, LogicHole

def case_to_if_tree(signal_map: dict[str, LogicNode]) -> None:
    """
    Rewrites CaseStatement nodes in-place inside the signal_map into nested LogicMux or LogicOp trees.
    This must be called before BDD, hash, or sympy emit.
    """
    for name, tree in list(signal_map.items()):
        if isinstance(tree, CaseStatement):
            selector = tree.selector
            mux_tree = None
            ##default_val = LogicHole()  # fallback if selector matches nothing
            default_val = LogicConst(0)  # fallback if selector matches nothing

            # reverse to preserve priority order for left-associative mux
            for item in reversed(tree.items):
                if not isinstance(item.body, LogicAssign):
                    raise TypeError(f"Expected LogicAssign in Case body, got {type(item.body)}")

                assigned_expr = item.body.rhs

                # Support multiple labels (e.g., case 2, 3: ...)
                condition = None
                for label in item.labels:
                    eq = LogicOp("XNOR", [selector, label])  # XNOR(a, b) == ~(a ^ b)
                    condition = eq if condition is None else LogicOp("OR", [condition, eq])

                mux_tree = LogicOp("MUX", [condition, assigned_expr, mux_tree or default_val])

            signal_map[name] = mux_tree

#def case_to_if_tree(case_stmt: CaseStatement) -> LogicNode:
#    selector = case_stmt.selector
#    items = case_stmt.items
#    else_branch = case_stmt.default or LogicHole("no_match")
#
#    for match_expr, result in reversed(items):
#        condition = LogicOp("XNOR", [selector, match_expr])
#        else_branch = LogicOp("IF", [condition, result, else_branch])
#
#    return else_branch

