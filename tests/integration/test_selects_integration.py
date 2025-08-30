import pytest

from logictree.eval import evaluate
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect

pytestmark = [pytest.mark.integration]


def test_bitselect_in_case_freevars_and_writes():
    s = LogicVar("s")
    y = LogicVar("y")

    bit0 = BitSelect(s, 0)

    case = CaseStatement(
        selector=s,
        items=[
            CaseItem(labels=[LogicConst(0)], body=[LogicAssign(lhs=y, rhs=bit0)], default=False)
        ],
        default=None
    )

    # free_vars should include s (selector + base of BitSelect)
    assert {v.name for v in case.free_vars()} == {"s"}
    # writes should include y
    assert {v.name for v in case.writes()} == {"y"}


def test_partselect_in_if_freevars_and_writes():
    s = LogicVar("s")
    y = LogicVar("y")

    slc = PartSelect(s, 7, 4)
    stmt = IfStatement(
        cond=LogicConst(1),
        then_branch=LogicAssign(lhs=y, rhs=slc),
        else_branch=None
    )

    # free_vars should include both s and the const cond
    fvs = {v.name for v in stmt.free_vars()}
    assert "s" in fvs
    # writes should include y
    assert {v.name for v in stmt.writes()} == {"y"}


def test_concat_in_case_freevars_and_writes():
    a = LogicVar("a")
    b = LogicVar("b")
    y = LogicVar("y")

    concat = Concat([a, PartSelect(b, 3, 0), LogicConst(1)])

    case = CaseStatement(
        selector=a,
        items=[
            CaseItem(labels=[LogicConst(1)], body=[LogicAssign(lhs=y, rhs=concat)], default=False)
        ],
        default=None
    )

    # free_vars should include a and b
    assert {v.name for v in case.free_vars()} == {"a", "b"}
    # writes should include y
    assert {v.name for v in case.writes()} == {"y"}

def test_evaluate_eqop_with_bitselect_true_and_false():
    s = LogicVar("s")
    bit1 = BitSelect(s, 1)

    expr = EqOp(bit1, LogicConst(1))

    env_true = {"s[1]": 1}
    env_false = {"s[1]": 0}

    assert evaluate(expr, env_true) == 1
    assert evaluate(expr, env_false) == 0


def test_evaluate_concat_inside_case():
    a, b, y = LogicVar("a"), LogicVar("b"), LogicVar("y")
    concat = Concat([a, b])

    case = CaseStatement(
        selector=a,
        items=[
            CaseItem(labels=[LogicConst(1)],
                     body=[LogicAssign(lhs=y, rhs=concat)],
                     default=False)
        ],
        default=None
    )

    env = {"a": 1, "b": 0}
    assert {v.name for v in case.free_vars()} == {"a", "b"}
    # Evaluate the assignment body
    #stmts = case.items[0].body
    stmt = case.items[0].body[0]
    assert isinstance(stmt, LogicAssign)
    rhs = stmt.rhs
    result = evaluate(rhs, env)
    # Expect Concat {a,b} → logically "10" in binary → decimal 2
    assert result == 2
