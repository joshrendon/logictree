import unittest
from antlr4 import *
from grammar.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from grammar.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder

class TestSystemVerilogParser(unittest.TestCase):
    def test_simple_module(self):
        code = "module foo(input logic a, output logic b); assign b = a; endmodule"
        input_stream = InputStream(code)
        lexer = SystemVerilogSubsetLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SystemVerilogSubsetParser(stream)
        tree = parser.compilation_unit()
        ast = ASTBuilder().visit(tree)
        self.assertEqual(ast[0].name, "foo")
        self.assertEqual(ast[0].ports, ["a", "b"])
        self.assertEqual(len(ast[0].items), 1)
