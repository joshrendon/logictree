from logictree.utils.overlay import overlay
from logictree.nodes import LogicVar
from logictree.utils.overlay import get_label, set_label

def test_no_overlay_methods_on_base_node():
    x = LogicVar("x")


    assert not hasattr(x, "viz_label")
    assert not hasattr(x, "set_viz_label")
    assert not hasattr(x, "get_metric")

    assert set_label(x) == "x"
    set_label(x, "input_x")
    assert get_label(x) == "input_x"
    

def test_overlay_registry_behavior():
    x = LogicVar("x")
    assert overlay.get_label(x) == "x"

    overlay.set_label(x, "input:x")
    assert overlay.get_label(x) == "input:x"

    overlay.clear_all()
    assert overlay.get_label(x) == "x"
