# tests/test_immutability.py
import pytest
from logictree.nodes.ops import LogicVar, LogicConst

def test_logicvar_frozen():
    v = LogicVar("a", width=1)
    with pytest.raises(Exception):
        v.name = "b"

def test_logicconst_frozen():
    c = LogicConst(3, width=2)
    with pytest.raises(Exception):
        c.value = 0
