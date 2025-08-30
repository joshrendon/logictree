import pytest

from logictree.eval import evaluate
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect

pytestmark = [pytest.mark.unit]


def test_bitselect_eval_true_and_false():
    s = LogicVar("s")
    b0 = BitSelect(s, 0)
    b1 = BitSelect(s, 1)

    env = {"s[0]": 1, "s[1]": 0}
    assert evaluate(b0, env) == 1
    assert evaluate(b1, env) == 0


def test_partselect_eval_high_and_low_bits():
    s = LogicVar("s")
    slc = PartSelect(s, 3, 0)

    # s[3:0] = 1010b → expect decimal 10
    env = {f"s[{i}]": bit for i, bit in enumerate([0, 1, 0, 1])}
    assert evaluate(slc, env) == 0b1010


def test_concat_eval_simple_two_bits():
    a, b = LogicVar("a"), LogicVar("b")
    concat = Concat([a, b])

    env = {"a": 1, "b": 0}
    # Expect binary "10" = 2
    assert evaluate(concat, env) == 0b10


def test_concat_eval_mixed_with_const():
    a, b = LogicVar("a"), LogicVar("b")
    concat = Concat([a, LogicConst(1), b])

    env = {"a": 1, "b": 0}
    # Expect a=1, const=1, b=0 → "110" = 6
    assert evaluate(concat, env) == 0b110


def test_eqop_with_bitselect_inside():
    s = LogicVar("s")
    b1 = BitSelect(s, 1)
    expr = EqOp(b1, LogicConst(1))

    env_true = {"s[1]": 1}
    env_false = {"s[1]": 0}
    assert evaluate(expr, env_true) == 1
    assert evaluate(expr, env_false) == 0


def test_eqop_with_partselect_inside():
    s = LogicVar("s")
    slc = PartSelect(s, 3, 0)
    expr = EqOp(slc, LogicConst(0b1010))

    env = {f"s[{i}]": bit for i, bit in enumerate([0, 1, 0, 1])}
    assert evaluate(expr, env) == 1  # matches 0b1010


# --- Width inference tests (new) ---

def test_logicconst_width_inference_and_repr():
    c0 = LogicConst(0)
    c5 = LogicConst(5)   # 0b101 → needs 3 bits
    c10 = LogicConst(10) # 0b1010 → needs 4 bits

    assert c0.width == 1
    assert c5.width == 3
    assert c10.width == 4

    # Repr includes width
    assert repr(c10) == "4'd10"


def test_concat_width_propagation_with_const_and_vars():
    a, b = LogicVar("a"), LogicVar("b")
    const = LogicConst(10)  # width=4
    concat = Concat([a, const, b])

    env = {"a": 1, "b": 1}
    val = evaluate(concat, env)

    # Expect "1 1010 1" = binary 110101 = decimal 53
    assert val == 0b110101

    # Ensure the total width = 1 (a) + 4 (const) + 1 (b) = 6 bits
    # Value should not exceed 6-bit maximum (63)
    assert val < (1 << 6)
