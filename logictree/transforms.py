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
        return ops.LogicOp(tree.op, new_children)
    else:
        return tree

def lower_case_statements_in_signal_map(signal_map: dict[str, LogicTreeNode]) -> None:
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

def case_to_if_tree(case_stmt) -> LogicTreeNode:
    from logictree.nodes.control.case import CaseStatement
    from logictree.nodes.control.ifstatement import IfStatement
    from logictree.nodes.ops.ops import LogicConst, LogicOp
    from pprint import pprint
    """Lower a CaseStatement node into a nested IfStatement tree."""
    log.info(f" Lowering CaseStatement with {len(case_stmt.items)} items")
    log.info(f"                             selector: {case_stmt.selector}")
    selector = case_stmt.selector
    items = case_stmt.items
    log.info(f"                             items: {items}")
    pprint(vars(case_stmt))

    def build_if_tree(index: int) -> LogicTreeNode:
        try:
            if index >= len(items):
                log.debug(f" build_if_tree({index}) reached end of branches")
                return None

            item = items[index]
            labels = item.labels
            stmt = item.body
            log.debug(f" build_if_tree({index}) labels: {labels}")
            log.debug(f" build_if_tree({index}) stmt: {stmt}")

            log.debug(f" build_if_tree({index}) LogicOp [EQ selector: {selector}, labels: {labels}]")
            conds = [LogicOp("EQ", [selector, LogicConst(label)]) for label in labels]
            log.debug(" stmt after conds")
            combined_cond = conds[0] if len(conds) == 1 else LogicOp("OR", conds)
            for c in conds:
                log.debug(f" cond type: {type(c)} val: {c}")

            log.debug(f" build_if_tree({index}) conds: {conds}")
            log.debug(f" build_if_tree({index}) combined_conds: {combined_cond}")
            log.debug(f"If node cond id: {id(combined_cond)}")

            then_branch = stmt.simplify() if hasattr(stmt, "simplify") else stmt
            else_branch = build_if_tree(index + 1)
            if isinstance(else_branch, IfStatement):
                else_branch._is_else_if = True

            log.debug(f" build_if_tree({index}) then_branch: {then_branch}")
            log.debug(f" build_if_tree({index}) else_branch: {else_branch}")

            if_node = IfStatement(
                cond=combined_cond,
                then_branch=then_branch,
                else_branch=else_branch,
            )

            from logictree.nodes.control.ifstatement import pretty_print_eq_label
            label_str = f"if({pretty_print_eq_label(if_node.cond)})"
            if_node.set_viz_label(label_str)
            log.debug(f"Set viz_label = {label_str} on id={id(if_node)}")

            if isinstance(if_node.cond, LogicTreeNode):
                log.debug("[build_if_tree] if_node.cond is LogicTreeNode!")
                if_node.set_viz_label(label_str)
                log.debug(f"[build_if_tree] Overriding label for {if_node.cond} → {if_node.cond.label()}")
            else:
                log.warning(f"Condition is not LogicTreeNode! Got{type(if_node.cond)}")

            log.debug(f" build_if_tree({index}) created IfStatement")

            log.debug("Final if_node.cond id: %s", id(if_node.cond))
            assert combined_cond is if_node.cond

            log.debug(f" Final IfStatement: then={if_node.then_branch}, else={if_node.else_branch}")
            
            return if_node
        except Exception as e:
            import traceback
            log.error(f" Exception in build_if_tree({index}): {e}")
            traceback.print_exc()
            return None

    return build_if_tree(0)

