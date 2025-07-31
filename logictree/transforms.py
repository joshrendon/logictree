from logictree.nodes import ops, control, base, hole
#from .nodes.base import LogicTreeNode

def lower_case_statements_in_signal_map(signal_map: dict[str, base.LogicTreeNode]) -> None:
    from logictree.nodes.control.case import CaseStatement
    from logictree.nodes.control.ifstatement import IfStatement
    from logictree.nodes.control.assign import LogicAssign
    from logictree.nodes.ops.ops import LogicConst, LogicOp
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


def case_to_if_tree(case_stmt) -> base.LogicTreeNode:
    from logictree.nodes.control.case import CaseStatement
    from logictree.nodes.control.ifstatement import IfStatement
    from logictree.nodes.ops.ops import LogicConst, LogicOp
    from pprint import pprint
    """Lower a CaseStatement node into a nested IfStatement tree."""
    print(f" Lowering CaseStatement with {len(case_stmt.items)} items")
    print(f"                             selector: {case_stmt.selector}")
    selector = case_stmt.selector
    items = case_stmt.items
    print(f"                             items: {items}")
    pprint(vars(case_stmt))
    #print(f"                             branches: {branches}")

    #if not branches:
    #    log.warning("case_to_if_tree() branches not found")
    #    return case_stmt  # Nothing to lower

    def build_if_tree(index: int) -> base.LogicTreeNode:
        try:
            if index >= len(items):
                print(f"[DEBUG]: build_if_tree({index}) reached end of branches")
                return None

            #item = branches[index]
            item = items[index]
            labels = item.labels
            stmt = item.body
            print(f"DEBUG: build_if_tree({index}) labels: {labels}")
            print(f"DEBUG: build_if_tree({index}) stmt: {stmt}")

            conds = [LogicOp("EQ", [selector, LogicConst(label)]) for label in labels]
            print("DEBUG: stmt after conds")
            combined_cond = conds[0] if len(conds) == 1 else LogicOp("OR", conds)
            print(f"DEBUG: build_if_tree({index}) conds: {conds}")
            print(f"DEBUG: build_if_tree({index}) combined_conds: {combined_cond}")

            then_branch = stmt.simplify() if hasattr(stmt, "simplify") else stmt
            else_branch = build_if_tree(index + 1)
            if isinstance(else_branch, IfStatement):
                else_branch._is_else_if = True

            print(f"DEBUG: build_if_tree({index}) then_branch: {then_branch}")
            print(f"DEBUG: build_if_tree({index}) else_branch: {else_branch}")

            if_node = IfStatement(
                cond=combined_cond,
                then_branch=then_branch,
                else_branch=else_branch,
            )
            print(f"[DEBUG] build_if_tree({index}) created IfStatement")
            return if_node
        except Exception as e:
            import traceback
            print(f"[ERROR] Exception in build_if_tree({index}): {e}")
            traceback.print_exc()
            return None

    return build_if_tree(0)


