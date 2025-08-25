import pytest

from logictree.eval import evaluate
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.ops import LogicConst, LogicVar

pytestmark = [pytest.mark.unit]


def test_eqop_free_vars_and_writes():
    a = LogicVar("a")
    b = LogicVar("b")
    eq = EqOp(a, b)

    # Free vars are the union of operands
    fv = eq.free_vars()
    assert {v.name for v in fv} == {"a", "b"}

    # EqOp does not write anything
    assert eq.writes() == frozenset()
    assert eq.writes_must() == frozenset()


def test_eqop_evaluate_with_vars():
    a = LogicVar("a")
    b = LogicVar("b")
    eq = EqOp(a, b)

    # Evaluate with different environments
    assert evaluate(eq, {"a": 0, "b": 0}) == 1
    assert evaluate(eq, {"a": 1, "b": 1}) == 1
    assert evaluate(eq, {"a": 0, "b": 1}) == 0
    assert evaluate(eq, {"a": 1, "b": 0}) == 0


def test_eqop_evaluate_with_constants():
    a = LogicConst(1)
    b = LogicConst(1)
    c = LogicConst(0)

    eq1 = EqOp(a, b)
    eq2 = EqOp(a, c)

    assert evaluate(eq1, {}) == 1   # 1 == 1
    assert evaluate(eq2, {}) == 0   # 1 == 0


def test_eqop_str_and_label():
    a = LogicVar("x")
    b = LogicConst(0)
    eq = EqOp(a, b)

    s = str(eq)
    assert "==" in s and "x" in s

    # Label should just be "=="
    assert eq.label() == "=="
    assert eq.op == "=="
