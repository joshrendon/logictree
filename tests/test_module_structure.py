import pytest

pytestmark = [pytest.mark.unit]


from logictree.nodes.struct.module import Module
from logictree.pipeline import lower_sv_text_to_logic


def test_module_wrapper_structure():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    module_map = lower_sv_text_to_logic(code)
    mod = module_map["foo"]
    assert isinstance(mod, Module)

    assert "foo" in module_map
    mod = module_map["foo"]
    assert mod.name == "foo"
    assert "b" in mod.module_map
