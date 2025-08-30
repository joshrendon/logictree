import math

import pytest

from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect


# -----------------------------------------------------------------------------
# LogicConst width inference
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value, expected_width, expected_repr",
    [
        (0, 1, "1'd0"),   # special-case: zero always 1 bit
        (1, 1, "1'd1"),
        (2, 2, "2'd2"),
        (3, 2, "2'd3"),
        (4, 3, "3'd4"),
        (7, 3, "3'd7"),
        (8, 4, "4'd8"),
        (15, 4, "4'd15"),
    ],
)
def test_logicconst_width_inference(value, expected_width, expected_repr):
    c = LogicConst(value)
    assert c.width == expected_width
    assert repr(c) == expected_repr

    # double-check with formula
    inferred = max(1, math.ceil(math.log2(value + 1))) if value > 0 else 1
    assert c.width == inferred


# -----------------------------------------------------------------------------
# BitSelect always has width = 1
# -----------------------------------------------------------------------------
def test_bitselect_width_and_repr():
    s = LogicVar("s").with_width(8)
    sel = BitSelect(s, 3)
    assert sel.width == 1
    assert repr(sel) == "s[3]"


# -----------------------------------------------------------------------------
# PartSelect width depends on msb/lsb
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("msb, lsb, expected_width", [(7, 4, 4), (3, 0, 4), (0, 0, 1)])
def test_partselect_width_and_repr(msb, lsb, expected_width):
    s = LogicVar("s").with_width(8)
    sel = PartSelect(s, msb, lsb)
    assert sel.width == expected_width
    assert repr(sel) == f"s[{msb}:{lsb}]"


# -----------------------------------------------------------------------------
# Concat width = sum of part widths
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "parts, expected_width, expected_repr",
    [
        ([LogicVar("a").with_width(1), LogicVar("b").with_width(1)], 2, "{a, b}"),
        ([LogicVar("a").with_width(1), LogicConst(1), LogicVar("b").with_width(1)], 3, "{a, 1'd1, b}"),
        ([LogicConst(15), LogicConst(1)], 4 + 1, "{4'd15, 1'd1}"),
    ],
)
def test_concat_width_and_repr(parts, expected_width, expected_repr):
    c = Concat(parts)
    assert c.width == expected_width
    assert repr(c) == expected_repr
