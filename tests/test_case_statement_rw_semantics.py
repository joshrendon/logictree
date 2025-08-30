"""
Tests for CaseStatement read/write (RW) semantics.


These test validate how case statements interact with variable usage.
In particular, we check:

  * free_vars() → which LogicVars are referenced (selector + RHS expressions)
  * writes()   → which LogicVars may be assigned in any branch
  * writes_must() → which LogicVars are guaranteed to be assigned on *all*
                    possible execution paths

Key semantics being preserved:
  - Without a default branch, coverage is partial: must-writes is ∅ unless
    every case item writes to the same variable *and* the selector domain
    is considered closed.
  - With a default branch, coverage is total: any variable written by default
    plus at least one other branch is considered must-write, as are variables
    written by all branches.
  - Free-vars must always return LogicVar objects, never raw constants/strings.

These tests preserve intent for RW semantics, ensuring that the lowering,
analysis, and caching logic remain faithful to RTL expectations.
"""
import pytest

pytestmark = [pytest.mark.unit]

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.ops.ops import LogicConst, LogicVar


def test_case_statement_rw_with_default_total_assignment():
    case = CaseStatement(
        selector=LogicVar("sel"),
        items=(
            CaseItem(
                match=[LogicConst(0)], 
                labels=[LogicConst(0)],
                body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a")),
                default=False
            ),
            CaseItem(
                match=[LogicConst(1)],
                labels=[LogicConst(1)],
                body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("b")),
                default=False
            ),
        ),
        default=CaseItem(
            labels=[],
            body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("c")),
            default=True
        )
    )

    fv = case.free_vars()
    # free_vars should always return LogicVar objects (never raw strings/constants)
    assert all(isinstance(v, LogicVar) for v in fv), "free_vars() must return LogicVar objects!"
    # Selector + all RHS vars are observed in free_vars
    assert {v.name for v in case.free_vars()} == {"sel", "a", "b", "c"}
    # All branches assign to the same LHS: y
    assert {v.name for v in case.writes()} == {"y"}
    # Because a default exists, coverage is exhaustive → y is a must-write
    assert {v.name for v in case.writes_must()} == {"y"}, "Should be total because default is present"


def test_case_statement_rw_without_default_partial_assignment():
    case = CaseStatement(
        selector=LogicVar("sel"),
        items=[
            CaseItem(labels=[LogicConst(0)], body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a")), default=False),
            CaseItem(labels=[LogicConst(1)], body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("b")), default=False),
        ],
        default=None
    )

    # Selector and both RHS vars appear in free_vars
    assert {v.name for v in case.free_vars()} == {"sel", "a", "b"}
    # Both arms write to y
    assert {v.name for v in case.writes()} == {"y"}
    # No default → case is not exhaustive → must-writes should be empty
    assert case.writes_must() == frozenset(), "Must-writes should be empty (not all selector values covered)"


def test_case_statement_multiple_outputs_and_partial_must_write():
    case = CaseStatement(
        selector=LogicVar("mode"),
        items=[
            CaseItem(labels=[LogicConst(0)], body=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("x")), default=False),
            CaseItem(labels=[LogicConst(1)], body=LogicAssign(lhs=LogicVar("b"), rhs=LogicVar("y")), default=False),
        ],
        default=CaseItem(labels=[], body=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("z")), default=True),
    )

    # Collectively, assignments can reach both a and b
    assert {v.name for v in case.writes()} == {"a", "b"}
    # Only 'a' is guaranteed:
    #   - arm0 writes 'a'
    #   - default writes 'a'
    #   - 'b' is conditional (only in arm1)
    assert {v.name for v in case.writes_must()} == {"a"}, "Only 'a' is written in all paths; 'b' is conditional"
    # Free vars include selector and all RHS symbols
    assert {v.name for v in case.free_vars()} == {"mode", "x", "y", "z"}


def test_case_statement_single_branch_with_default_covers_all():
    case = CaseStatement(
        selector=LogicVar("mode"),
        items=(
            CaseItem(labels=[LogicConst(0)], body=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("x")), default=False),
        ),
        default=CaseItem(labels=[], body=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("z")), default=True),
    )

    # Both branches assign to 'a'
    assert {v.name for v in case.writes()} == {"a"}
    # Exhaustive coverage → 'a' is a must-write
    assert {v.name for v in case.writes_must()} == {"a"}, "Both branches assign 'a'"
    # Free vars include selector and both RHS vars
    assert {v.name for v in case.free_vars()} == {"mode", "x", "z"}
