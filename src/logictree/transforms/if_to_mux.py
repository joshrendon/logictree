import logging

from logictree.nodes import LogicMux
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.alwaysblock import BlockStatement
from logictree.nodes.control.assign import ProceduralAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import NotOp
from logictree.nodes.ops.ops import LogicConst, LogicVar

log = logging.getLogger(__name__)


def _extract_assigned_value(node, target_lhs_name: str | None) -> 'LogicTreeNode':
    """
    Convert a branch node (BlockStatement / ProceduralAssign / raw expr)
    to the single RHS value assigned to target_lhs_name (if provided).
    Falls back to EmptyBranch() when no assignment is found.
    """
    # Unwrap accidental 1-tuple
    if isinstance(node, tuple):
        if len(node) == 1:
            return _extract_assigned_value(node[0], target_lhs_name)
        # Multiple items in a tuple is unexpected here
        raise TypeError("Unexpected tuple of statements in branch lowering")

    # Direct RHS
    if isinstance(node, ProceduralAssign):
        return node.rhs

    # Block: find last assignment to target_lhs (or last assignment if none given)
    if isinstance(node, BlockStatement):
        assigns = [s for s in node.statements if isinstance(s, ProceduralAssign)]
        if not assigns:
            return EmptyBranch()

        if target_lhs_name is not None:
            filtered = []
            for s in assigns:
                lhs = s.lhs
                lhs_name = lhs.name if isinstance(lhs, LogicVar) else getattr(lhs, "name", None)
                if lhs_name == target_lhs_name:
                    filtered.append(s)
            assigns = filtered or assigns  # if none matched, keep all and take last

        return assigns[-1].rhs

    # Already a value (LogicVar, LogicConst, LogicMux, etc.)
    return node

def _simplify_eq_to_bool(cond):
    # Turn Eq(s, 0/1) (1-bit) into ~s / s
    if isinstance(cond, EqOp) and isinstance(cond.rhs, LogicConst):
        w = cond.rhs.width
        if w in (None, 1):
            val = cond.rhs.as_int() & 1
            return cond.lhs if val == 1 else NotOp(cond.lhs)
    return cond

def if_to_mux_tree(node, target_lhs_name: str | None = None) -> LogicTreeNode:
    """
    Recursively lower IfStatement to nested mux expressions.
    Expects node to be the rhs of a LogicAssign.
    """
    log.debug(f"[if_to_mux] node type: {type(node)}")
    #log.debug(f"then_branch: {node.then_branch}")
    #log.debug(f"else_branch: {node.else_branch}")
    if not isinstance(node, IfStatement):
        return _extract_assigned_value(node, target_lhs_name)
    if node.then_branch is None or node.else_branch is None:
        raise NotImplementedError("Only full if/else supported")

    cond = node.cond
    tval = if_to_mux_tree(node.then_branch, target_lhs_name)
    fval = if_to_mux_tree(node.else_branch, target_lhs_name) if node.else_branch is not None else EmptyBranch()

    # Normalize branches to single values
    tval = _extract_assigned_value(tval, target_lhs_name)
    fval = _extract_assigned_value(fval, target_lhs_name)

    return LogicMux(selector=cond, if_true=tval, if_false=fval)
