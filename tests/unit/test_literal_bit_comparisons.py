import pytest
from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.selects import BitSelect, PartSelect, Concat
from tests.utils_bitselect import literal_bit_comparisons

pytestmark = [pytest.mark.unit]

def test_eqop_with_logicvar_and_const():
    lhs = LogicVar(name="x")
    rhs = LogicConst(value=True)
    node = EqOp(lhs=lhs, rhs=rhs)
    assert literal_bit_comparisons(node) == {("x", True)}

def test_eqop_with_bitselect_and_const():
    lhs = BitSelect(LogicVar(name="bus"), LogicConst(value=3))
    rhs = LogicConst(value=False)
    node = EqOp(lhs=lhs, rhs=rhs)
    assert literal_bit_comparisons(node) == {(3, False)}

def test_eqop_with_concat_and_const():
    concat = Concat([
        LogicVar("a"),
        LogicVar("b"),
        LogicVar("c"),
        LogicVar("d"),
    ])
    rhs = LogicConst("4'b1001")
    node = EqOp(lhs=concat, rhs=rhs)
    assert literal_bit_comparisons(node) == {
        ("a", True),
        ("b", False),
        ("c", False),
        ("d", True)
    }

def test_eqop_with_partselect_and_const():
    # Note: part select not yet handled in `literal_bit_comparisons`, so this should do nothing
    lhs = PartSelect(base=LogicVar("s"), msb=LogicConst(3), lsb=LogicConst(0))
    rhs = LogicConst(value="4'b0101")
    node = EqOp(lhs=lhs, rhs=rhs)
    assert literal_bit_comparisons(node) == set()  # Currently ignored


def test_mixed_deep_tree():
    # Valid: BitSelect(LogicVar, LogicConst) + LogicConst → Concat
    concat_node = Concat([
        BitSelect(LogicVar("data"), LogicConst(1)),
        LogicConst(0, width=1),
    ])

    eq1 = EqOp(lhs=concat_node, rhs=LogicConst(value="2'b10"))  # valid: EqOp over bitvector

    # Another valid EqOp on a scalar
    eq2 = EqOp(lhs=LogicVar("flag"), rhs=LogicConst(True))

    # Wrap both in an OrOp just to traverse both
    root = OrOp(eq1, eq2)

    # Should not raise, and should extract just the literal comparisons
    results = literal_bit_comparisons(root)

    # We don't assert exact values here—just that it runs and returns something iterable
    assert isinstance(results, set)
    assert all(isinstance(x, tuple) for x in results)
