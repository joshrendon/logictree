import pytest
pytestmark = [pytest.mark.unit]

def test_logic_const_str():
    const = LogicConst(value="3'b101")
    assert str(const) == "3'b101"
    assert repr(const) == "LogicConst(3'b101)"
