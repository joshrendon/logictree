import pytest
pytestmark = [pytest.mark.unit]

import copy

from logictree.nodes.ops import LogicConst, LogicVar
from logictree.utils import overlay

def test_logicconst_overlay_behavior():
    c = LogicConst(1)

    # Test label setting
    c.set_viz_label("const one")
    assert c.label() == "const one"

    # Test expr source
    c.set_expr_source("1")
    assert c.get_expr_source() == "1"

    # Test metric cache
    c.cache_metrics(depth=3)
    assert c.get_metric("depth") == 3

    # Test clone preserves overlay
    c2 = c.clone()
    assert c2 is not c
    assert c2.label() == "const one"
    assert c2.get_expr_source() == "1"
    assert c2.get_metric("depth") == 3

    # Test deepcopy doesn’t crash
    d = copy.deepcopy(c)
    assert d.label() == "const one"

    # Hashability
    assert isinstance(hash(c), int)

def test_logicvar_overlay_behavior():
    v = LogicVar("foo")

    v.set_viz_label("signal foo")
    v.set_expr_source("foo_wire")
    v.cache_metrics(fan_in=2)

    assert v.label() == "signal foo"
    assert v.get_expr_source() == "foo_wire"
    assert v.get_metric("fan_in") == 2

    v2 = v.clone()
    assert v2.label() == "signal foo"
    assert v2.get_expr_source() == "foo_wire"

    d = copy.deepcopy(v)
    assert d.label() == "signal foo"
