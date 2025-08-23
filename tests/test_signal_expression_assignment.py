import pytest

pytestmark = [pytest.mark.unit]

from pprint import pprint

from antlr4 import *

from logictree.nodes.control.assign import LogicAssign
from logictree.pipeline import lower_sv_text_to_logic


def test_simple_module():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    module_map = lower_sv_text_to_logic(code)
    #print(f"DEBUG: code: {code}")
    pprint(module_map)

    assert "foo" in module_map
    mod = module_map["foo"]
    assign = mod.signal_map.get("b", LogicAssign("b"))
    print("assign:\n")
    pprint(assign)
    assert isinstance(assign, LogicAssign)
    assert assign.name == "a"

