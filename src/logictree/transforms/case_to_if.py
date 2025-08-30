"""
Case → If lowering transforms.

This module provides a clean separation of concerns:

  * case_to_if_tree(stmt): primitive lowering of a CaseStatement into an IfStatement
  * transform_cases(node): recursively walks an IR node and lowers any CaseStatements
  * lower_map_cases(signal_map): apply transform_cases across a dict[str, LogicTreeNode]
  * lower_module_cases(module): apply transform_cases to all assignments in a Module

Use case_to_if_tree() only when you know you have a CaseStatement.
Use transform_cases() (or the map/module variants) when you want to sanitize an
arbitrary node or structure that may contain CaseStatements.
"""

import logging

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseStatement  # your actual classes
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.struct.module import Module

log = logging.getLogger(__name__)


def case_to_if_tree(stmt: CaseStatement) -> IfStatement:
    """
    Lower a single CaseStatement into a nested IfStatement chain.

    Each case item is translated into an `if (selector == label)` branch,
    chained with `else if` for subsequent items. A default is lowered
    into a final unconditional branch.
    """
    assert isinstance(stmt, CaseStatement)

    current = None
    # Iterate reversed so the first item ends up outermost
    for item in reversed(stmt.items):
        cond = EqOp(stmt.selector, item.labels[0])
        current = IfStatement(cond=cond, then_branch=item.body, else_branch=current)

    # Default case: unconditional if(true)
    if stmt.default:
        current = IfStatement(
            cond=LogicConst(True),
            then_branch=stmt.default.body,
            else_branch=current,
        )

    return current


def transform_cases(node: LogicTreeNode) -> LogicTreeNode:
    """
    Recursively transform a LogicTreeNode, lowering all CaseStatements into IfStatements.
    Returns a structurally equivalent node tree with no CaseStatements.
    """
    if isinstance(node, CaseStatement):
        return case_to_if_tree(node)

    if isinstance(node, IfStatement):
        return IfStatement(
            cond=transform_cases(node.cond),
            then_branch=transform_cases(node.then_branch),
            else_branch=transform_cases(node.else_branch) if node.else_branch else None,
        )

    if isinstance(node, LogicAssign):
        return LogicAssign(
            lhs=node.lhs,
            rhs=transform_cases(node.rhs),
        )

    # short-circut for atomic leaves
    if isinstance(node, (LogicConst, LogicVar)):
        return node

    # Generic n-ary operator
    if hasattr(node, "children") and isinstance(node.children, (list, tuple)):
        new_children = [transform_cases(c) for c in node.children]
        return type(node)(*new_children)

    # Leaf or unhandled node → return unchanged
    return node


def lower_map_cases(signal_map: dict[str, LogicTreeNode]) -> dict[str, LogicTreeNode]:
    """
    Apply transform_cases() to each entry in a signal map.
    """
    return {name: transform_cases(tree) for name, tree in signal_map.items()}


def lower_module_cases(m: Module) -> Module:
    """
    Apply transform_cases() to all assignments in a Module.
    Returns a shallow copy with transformed assignment expressions.
    """
    new_assigns = {k: transform_cases(v) for k, v in m.assignments.items()}
    return Module(
        name=m.name,
        ports=m.ports,
        signal_map=m.signal_map,
        assignments=new_assigns,
        instances=m.instances,
    )
