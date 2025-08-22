# sv_parser/parse.py
from antlr4 import FileStream, InputStream, CommonTokenStream
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

def lower_module_declaration(tree):
    module_ctx = None
    for child in tree.getChildren():
        if isinstance(child, SystemVerilogSubsetParser.Module_declarationContext):
            module_ctx = child
            break
    if module_ctx is None:
        raise RuntimeError("No module_declaration found in parsed file.")

    selected_tree = lowerer.visitModule_declaration(module_ctx)
    print(f"Module: {lowerer.module_name}")
    MODULE_NAME = lowerer.module_name
    return selected_tree

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
