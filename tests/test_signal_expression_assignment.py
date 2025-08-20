import unittest
from antlr4 import *
from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from logictree.nodes.ops import LogicVar
from pprint import pprint

def test_simple_module():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    signal_map = lower_sv_text_to_logic(code)
    print(f"DEBUG: code: {code}")
    print(f"type(signal_map): {type(signal_map)}")
    print(f"signal_map keys: {list(signal_map.keys())}")
    pprint(signal_map)

    assert "out" in signal_map
    logic = signal_map["out"]
    assert isinstance(logic, LogicVar)
    assert logic.name == "a"

