import pytest

pytestmark = [pytest.mark.unit]

from tests.utils import LogicConstSV


def test_logic_const_str():
    const = LogicConstSV("3'b101")
    assert const.value == 5 and const.width == 3
    assert str(const) == "3'b101"
    assert repr(const) == "3'd5"
