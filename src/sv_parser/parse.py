from antlr4 import CommonTokenStream, FileStream, InputStream

from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser


def parse_sv_file(path: str):
    """Parse a SystemVerilog file into an ANTLR parse tree (compilation_unit)."""
    input_stream = FileStream(path)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    return parser.compilation_unit()


def parse_sv_text(src: str):
    """Parse SystemVerilog source text into an ANTLR parse tree (compilation_unit)."""
    input_stream = InputStream(src)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    return parser.compilation_unit()


def first_module_declaration(tree):
    """
    Breadth-first search for the first SystemVerilog 'module_declaration' context.
    Raises RuntimeError if none is found.
    """
    from collections import deque

    q = deque([tree])
    while q:
        node = q.popleft()
        # match the exact parser context type
        if isinstance(node, SystemVerilogSubsetParser.Module_declarationContext):
            return node
        # push children if any
        if hasattr(node, "getChildren"):
            q.extend(list(node.getChildren()))
    raise RuntimeError("No module_declaration found in parsed tree.")
