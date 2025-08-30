import pytest

from logictree.nodes import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar

pytestmark = [pytest.mark.unit]

def test_mux_to_primitives():

    s = LogicVar("s")
    a = LogicConst(1)
    b = LogicConst(0)

    mux = LogicMux(selector=s, if_true=a, if_false=b)
    prim = mux.to_primitives()

    # Should be Or(And(s, 1), And(~s, 0)) which simplifies to s
    assert prim is not None
    assert "AndOp" in repr(prim) or "OrOp" in repr(prim)
