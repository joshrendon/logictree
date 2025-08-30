# tests/test_serialize.py
from logictree.nodes import AndOp, LogicVar
from logictree.utils.overlay import set_label
from logictree.utils.serialize import logic_tree_to_json

#from logictree.utils.visual import label_for, set_label

def test_serialize_simple_and_gate():
    a = LogicVar("a")
    b = LogicVar("b")
    and_node = AndOp(a, b)

    # Register label for AndOp via overlay
    set_label(and_node, f"{a.name} & {b.name}")
    #overlay.set_label(and_node, f"{a.name} & {b.name}")

    result = logic_tree_to_json(and_node)

    assert result["type"] == "AndOp"
    assert result["label"] == "a & b"
    assert result["children"][0]["label"] == "a"
    assert result["children"][1]["label"] == "b"
