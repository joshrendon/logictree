import pytest

pytestmark = [pytest.mark.unit]

import unittest

from logictree.pipeline import lower_sv_text_to_logic


class TestSystemVerilogParser(unittest.TestCase):
    def test_simple_module(self):
        code = "module foo(input logic a, output logic b); assign b = a; endmodule"
        module_map = lower_sv_text_to_logic(code)
        #pprint(module_map)

        #for k, v in module_map.items():
        #    print(f"{k}: {type(v)}, label={getattr(v, 'label', lambda: '?')()}")
        mod = module_map["foo"]
        assert mod.name == "foo"
        assert mod.assignments['b'].__class__.__name__ == "LogicAssign"

