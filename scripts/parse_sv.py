from antlr4 import *
import sys
from pathlib import Path

# Dynamically add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from sv_parser.visitor import ASTBuilder
from pprint import pprint
from to_dot_util import to_dot

def parse_sv_file(filename):
    with open(filename, "r") as f:
        code = f.read()

    input_stream = InputStream(code)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    tree = parser.compilation_unit()

    visitor = ASTBuilder()
    ast = visitor.visit(tree)

    return ast

if __name__ == "__main__":
    path = sys.argv[1]
    ast = parse_sv_file(path)
    pprint(ast)

    # Build and render dot graph
    dot = to_dot(ast)
    dot.render("ast_output", format="png", cleanup=False)
    print("Saved graph to ast_output.png")

