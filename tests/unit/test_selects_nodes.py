import pytest

from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect

pytestmark = [pytest.mark.unit]


def test_bitselect_repr_and_equality():
    s = LogicVar("s")
    b0 = BitSelect(s, 0)
    b0_again = BitSelect(s, 0)
    b1 = BitSelect(s, 1)

    # repr and default_label
    assert repr(b0) == "s[0]"
    assert b0.default_label() == "s[0]"

    # equality + hash
    assert b0 == b0_again
    assert b0 != b1
    assert len({b0, b0_again, b1}) == 2

    # free_vars
    assert b0.free_vars() == {s}


def test_partselect_repr_and_equality():
    s = LogicVar("s")
    slc1 = PartSelect(s, 7, 4)
    slc2 = PartSelect(s, 7, 4)
    slc3 = PartSelect(s, 3, 0)

    # repr and default_label
    assert repr(slc1) == "s[7:4]"
    assert slc1.default_label() == "s[7:4]"

    # equality + hash
    assert slc1 == slc2
    assert slc1 != slc3
    assert len({slc1, slc2, slc3}) == 2

    # free_vars
    assert slc1.free_vars() == {s}


def test_concat_repr_and_free_vars():
    a = LogicVar("a")
    b = LogicVar("b")
    part = PartSelect(b, 3, 0)
    const = LogicConst(1)

    concat1 = Concat([a, part, const])
    concat2 = Concat([a, part, const])
    concat3 = Concat([a, const])  # shorter

    # repr and default_label
    expected_str = f"{{a, b[3:0], {repr(const)}}}"
    assert repr(concat1) == expected_str
    assert concat1.default_label() == expected_str

    # equality + hash
    assert concat1 == concat2
    assert concat1 != concat3
    assert len({concat1, concat2, concat3}) == 2

    # free_vars: includes both a and b
    fvs = {v.name for v in concat1.free_vars()}
    assert fvs == {"a", "b"}
