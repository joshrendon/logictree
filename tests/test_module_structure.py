import pytest

pytestmark = [pytest.mark.unit]

from antlr4 import *

from logictree.pipeline import lower_sv_text_to_logic


def test_module_wrapper_structure():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    module_map = lower_sv_text_to_logic(code)
    mod = module_map["m"]
    assert isinstance(mod, Module)
    y = mod.signal_map["y"]

    assert "foo" in modules
    mod = modules["foo"]
    assert mod.name == "foo"
    assert "b" in mod.signal_map
