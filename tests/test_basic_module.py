import unittest
from antlr4 import *
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder
from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from pprint import pprint

class TestSystemVerilogParser(unittest.TestCase):
    def test_simple_module(self):
        code = "module foo(input logic a, output logic b); assign b = a; endmodule"
        input_stream = InputStream(code)
        lexer = SystemVerilogSubsetLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SystemVerilogSubsetParser(stream)
        tree = parser.compilation_unit()

        module_map = lower_sv_text_to_logic(code)
        print(f"DEBUG: code: {code}")
        print(f"type(module_map): {type(module_map)}")
        print(f"module_map keys: {list(module_map.keys())}")
        pprint(module_map)

        for k, v in module_map.items():
            print(f"{k}: {type(v)}, label={getattr(v, 'label', lambda: '?')()}")
        mod = module_map["foo"]
        assert mod.name == "foo"
        assert mod.assignments['b'].__class__.__name__ == "LogicAssign"

        #ast = ASTBuilder().visit(tree)
        #print(f"dir(ast):{dir(ast)}")
        #self.assertEqual(ast["op"], "foo")
        #self.assertEqual(ast.ports, ["a", "b"])
        #self.assertEqual(len(ast.items), 1)
