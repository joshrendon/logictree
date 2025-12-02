# utils/assertion.py
"""
Assertion and analysis utilities for LogicTree structures.

These helpers are primarily for use in unit tests and smoke tests
to validate correctness of lowering passes and structural invariants.

Example:
    mux = LogicMux(selector=Eq(sel, 0),
                   if_true=LogicVar("a"),
                   if_false=LogicMux(selector=Eq(sel, 1),
                                     if_true=LogicVar("b"),
                                     if_false=EmptyBranch()))
    assert collect_mux_leaf_labels(mux) == {"a", "b", "<empty>"}
    assert collect_mux_conditions(mux) == {"sel == 1'b0", "sel == 1'b1"}
"""
import logging
from itertools import product
from typing import Dict, List, Set

import sympy as sp
from sympy.logic.boolalg import S

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.if_to_mux import if_to_mux_tree
from logictree.transforms.to_primitives import to_primitives
from logictree.utils.display import pretty_print

log = logging.getLogger(__name__)


def evaluate_logic_tree(node, env: Dict[str, int]) -> int:
    """Evaluate a LogicTreeNode with a given variable environment mapping {var: value}."""
    if isinstance(node, LogicVar):
        return int(env[node.name])
    elif isinstance(node, LogicConst):
        return int(node.value)
    elif isinstance(node, EmptyBranch):
        return 0  # treat empty as 0
    elif isinstance(node, AndOp):
        return evaluate_logic_tree(node.operands[0], env) & evaluate_logic_tree(node.operands[1], env)
    elif isinstance(node, OrOp):
        return evaluate_logic_tree(node.operands[0], env) | evaluate_logic_tree(node.operands[1], env)
    elif isinstance(node, NotOp):
        return (~evaluate_logic_tree(node.operand, env)) & 1
    elif isinstance(node, EqOp):
        return int(evaluate_logic_tree(node.lhs, env) == evaluate_logic_tree(node.rhs, env))
    elif isinstance(node, NeqOp):
        return int(evaluate_logic_tree(node.lhs, env) != evaluate_logic_tree(node.rhs, env))
    elif isinstance(node, XorOp):
        return evaluate_logic_tree(node.operands[0], env) ^ evaluate_logic_tree(node.operands[1], env)
    elif isinstance(node, XnorOp):
        return int(not (evaluate_logic_tree(node.operands[0], env) ^ evaluate_logic_tree(node.operands[1], env)))
    elif isinstance(node, LogicMux):
        sel = evaluate_logic_tree(node.selector, env)
        return evaluate_logic_tree(node.if_true, env) if sel else evaluate_logic_tree(node.if_false, env)
    elif isinstance(node, IfStatement):
        cond = evaluate_logic_tree(node.cond, env)
        return evaluate_logic_tree(node.then_branch, env) if cond else evaluate_logic_tree(node.else_branch, env)
    elif isinstance(node, LogicAssign):
        return evaluate_logic_tree(node.rhs, env)
    else:
        raise TypeError(f"Unsupported node type in evaluation: {type(node)}")

def exhaustive_input_equiv(lhs, rhs, inputs, verbose: bool = True) -> bool:
    """
    Exhaustively evaluate lhs and rhs LogicTreeNodes across all combinations of inputs.
    Returns True if equivalent, False otherwise.
    """
    n = len(inputs)
    total_cases = 2 ** n
    mismatches = 0

    # Walk the truth table
    for i, values in enumerate(product([0, 1], repeat=n), start=1):
        env = dict(zip(inputs, values))
        lhs_val = evaluate_logic_tree(lhs, env)
        rhs_val = evaluate_logic_tree(rhs, env)

        if lhs_val != rhs_val:
            mismatches += 1
            if verbose:
                log.error(f"[Mismatch] Case {i}/{total_cases}, env={env}, lhs={lhs_val}, rhs={rhs_val}")

        elif verbose and total_cases <= 16:  # log all if small table, else skip spam
            log.debug(f"[Match] Case {i}/{total_cases}, env={env}, out={lhs_val}")

    if verbose:
        if mismatches == 0:
            log.info(f" Exhaustive equivalence check passed for {total_cases} input cases.")
        else:
            log.warning(f" Found {mismatches} mismatches out of {total_cases} cases.")

    return mismatches == 0

def sorted_mux_labels(mux: LogicMux) -> List[str]:
    return sorted(collect_mux_leaf_labels(mux))

def sorted_mux_conditions(mux: LogicMux) -> List[str]:
    return sorted(collect_mux_conditions(mux))

def collect_mux_leaf_labels(mux: LogicMux) -> Set[str]:
    """
    Recursively collect the labels from the leaf outputs of a mux tree.
    """
    labels = set()

    def _collect(node):
        if isinstance(node, LogicVar):
            labels.add(node.name)
        elif isinstance(node, EmptyBranch):
            labels.add("<empty>")
        elif isinstance(node, LogicMux):
            _collect(node.if_true)
            _collect(node.if_false)
        # Optional: warn on unexpected node types

    _collect(mux)
    return labels

def collect_mux_conditions(mux: LogicMux) -> Set[str]:
    """Collect all selector conditions used in a mux chain."""
    conditions = set()
    current = mux

    while isinstance(current, LogicMux):
        conditions.add(current.selector.label())
        current = current.if_false

    return conditions

# ------------------------------------------------------------------------------
# Assertion helpers
# ------------------------------------------------------------------------------
def assert_mux_has_leaves(mux: LogicMux, expected: Set[str]):
    """Assert that the mux chain produces exactly the given leaf labels."""
    labels = collect_mux_leaf_labels(mux)
    assert labels == expected, f"Expected leaf labels {expected}, got {labels}"


def assert_mux_has_conditions(mux: LogicMux, expected: Set[str]):
    """Assert that the mux chain produces exactly the given selector conditions."""
    conditions = collect_mux_conditions(mux)
    assert conditions == expected, f"Expected conditions {expected}, got {conditions}"


def assert_mux_path_depth(mux: LogicMux, max_depth: int):
    """
    Assert that the depth of the mux chain (longest if_false chain) does not
    exceed max_depth. Useful for catching unintended nested mux blowups.
    """
    depth = 0
    node = mux
    while isinstance(node, LogicMux):
        depth += 1
        node = node.if_false
    assert depth <= max_depth, f"Mux path depth {depth} exceeds max {max_depth}"

# === Sympy Integration ===
def to_sympy_expr(node: LogicTreeNode) -> sp.Expr:
    """
    Convert a LogicTreeNode (CaseStatement, LogicMux, or primitive-lowered tree)
    into a sympy Boolean expression.
    """
    from logictree.transforms.to_sympy import to_sympy_expr as _to_sympy_expr
    return _to_sympy_expr(node)

def assert_logic_equiv(lhs: LogicTreeNode, rhs: LogicTreeNode) -> None:
    lhs_expr = to_sympy_expr(lhs)
    rhs_expr = to_sympy_expr(rhs)

    diff = lhs_expr ^ rhs_expr
    #diff = simplify_logic(Eq(lhs_expr, rhs_expr))
    #assert diff == True
    simplified = sp.simplify_logic(diff, form='dnf')

    # Debug traces
    log.debug("\n[assert_logic_equiv DEBUG]")
    log.debug("LHS expr: %s", lhs_expr)
    log.debug("RHS expr: %s", rhs_expr)
    log.debug("XOR diff: %s", diff)
    log.debug("Simplified diff: %s %s", simplified, type(simplified))

    if simplified not in (False, S.false):
        raise AssertionError(
            f"Logic trees not equivalent!\n\n"
            f"LHS:\n{pretty_print(lhs)}\n\n"
            f"RHS:\n{pretty_print(rhs)}\n\n"
            f"Sympy check: {simplified}"
        )

def assert_case_equivalence(case_stmt: CaseStatement) -> None:
    """
    Check that a CaseStatement lowers consistently to mux and primitives.
    """
    # Case → If → Mux
    if_tree = case_to_if_tree(case_stmt)
    mux_tree = if_to_mux_tree(if_tree)
    prim_tree = to_primitives(mux_tree)

    # Compare Case vs Mux
    assert_logic_equiv(case_stmt, mux_tree)

    # Compare Mux vs Primitives
    assert_logic_equiv(mux_tree, prim_tree)

    # Optionally: Case vs Primitives directly
    assert_logic_equiv(case_stmt, prim_tree)

def assert_mux_equivalence(mux1: LogicMux, mux2: LogicMux):
    """
    Placeholder for full logical equivalence checking between two mux trees.
    TODO: later back with sympy / truth table / BDD equivalence engines.
    """
    leaves1 = collect_mux_leaf_labels(mux1)
    leaves2 = collect_mux_leaf_labels(mux2)
    conds1 = collect_mux_conditions(mux1)
    conds2 = collect_mux_conditions(mux2)

    assert leaves1 == leaves2, f"Leaf sets differ: {leaves1} vs {leaves2}"
    assert conds1 == conds2, f"Condition sets differ: {conds1} vs {conds2}"
    # This is structural, not semantic equivalence — refine later.

