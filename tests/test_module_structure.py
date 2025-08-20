import unittest
from antlr4 import *
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder
from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from pprint import pprint

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
