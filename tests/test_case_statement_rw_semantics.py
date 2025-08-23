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
                match=LogicConst(0), 
                labels=[LogicConst(0)],
                body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a")),
                default=False
            ),
            CaseItem(
                match=LogicConst(1),
                labels=[LogicConst(1)],
                body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("b")),
                default=False
            ),
        ),
        default=CaseItem(
            match=LogicConst(0), #dummy match
            labels=[LogicConst(0)], #dummy
            body=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("c")),
            default=True
        )
    )

    fv = case.free_vars()
    #print("free_vars raw:", case.free_vars())
    #print("free_vars names:", {v.name for v in case.free_vars()})
    #for v in case.free_vars():
    #    print(f"case.free_vars.v: {v}")
    #    if not isinstance(v, LogicVar):
    #        print("! Non-LogicVar in free_vars:", type(v), v)

    assert all(isinstance(v, LogicVar) for v in fv), "free_vars() must return LogicVar Objects!"
    assert {v.name for v in case.free_vars()} == {"sel", "a", "b", "c"}
    assert {v.name for v in case.writes()} == {"y"}
    assert {v.name for v in case.writes_must()} == {"y"}, "Should be total because default is present"

#def test_case_statement_rw_without_default_partial_assignment():
#    from logictree.nodes.ops.ops import LogicVar, LogicConst
#    case = CaseStatement(
#        selector=LogicVar("sel"),
#        items=(
#            CaseItem(LogicConst(0), LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a"))),
#            CaseItem(LogicConst(1), LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("b"))),
#        ),
#        default=None
#    )
#
#    assert {v.name for v in case.free_vars()} == {"sel", "a", "b"}
#    assert {v.name for v in case.writes()} == {"y"}
#    assert case.writes_must() == frozenset(), "Must-writes should be empty (not all selector values covered)"
#
#def test_case_statement_multiple_outputs_and_partial_must_write():
#    from logictree.nodes.ops.ops import LogicVar, LogicConst
#    case = CaseStatement(
#        selector=LogicVar("mode"),
#        items=(
#            CaseItem(LogicConst(0), LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("x"))),
#            CaseItem(LogicConst(1), LogicAssign(lhs=LogicVar("b"), rhs=LogicVar("y"))),
#        ),
#        default=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("z")),
#    )
#
#    assert {v.name for v in case.writes()} == {"a", "b"}
#    assert {v.name for v in case.writes_must()} == {"a"}, "Only 'a' is written in all paths; 'b' is conditional"
#    assert {v.name for v in case.free_vars()} == {"mode", "x", "y", "z"}
#
#def test_case_statement_single_branch_with_default_covers_all():
#    from logictree.nodes.ops.ops import LogicVar, LogicConst
#    case = CaseStatement(
#        selector=LogicVar("mode"),
#        items=(
#            CaseItem(LogicConst(0), LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("x"))),
#        ),
#        default=LogicAssign(lhs=LogicVar("a"), rhs=LogicVar("z")),
#    )
#
#    assert {v.name for v in case.writes()} == {"a"}
#    assert {v.name for v in case.writes_must()} == {"a"}, "Both branches assign 'a'"
#    assert {v.name for v in case.free_vars()} == {"mode", "x", "z"}
