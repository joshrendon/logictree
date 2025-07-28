import argparse
import logging
from antlr4 import FileStream, CommonTokenStream
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder, lower_stmt_to_logic_tree
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from logictree.graphviz_utils import to_svg, to_png
from logictree.utils import (
    balanced_tree_reduce,
    get_logic_hash,
    explain_logic_hash,
    explain_expr_tree,
    to_sympy_expr,
    pretty_print,
    to_dot
)
from logictree.nodes import repair_tree_inputs, gate_summary, LogicOp
from utils.graphviz_export import logic_tree_to_dot, save_dot_svg_png
from utils.utils_cli import write_golden_file
from utils.ascii_tree import logic_tree_to_ascii, to_ascii

import json
from pprint import pprint

log = logging.getLogger(__name__)

def parse_sv_file(path):
    input_stream = FileStream(path)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    return parser.compilation_unit()

def lower_sv_ast_to_signal_map(tree):
    lowerer = SVToLogicTreeLowerer()
    return lowerer.collect_signals(tree)

def handle_output(signal_map, args):
    for name, tree in signal_map.items():
        if args.debug_log:
            logging.basicConfig(level=logging.DEBUG,
                                format="%(levelname)s:%(name)s: %(message)s")
        else:
            logging.basicConfig(level=logging.INFO,
                                format="%(message)s")

        if args.hash_tree or args.dump_all:
            print(f"Hash for {name}: {get_logic_hash(tree)}")

        if args.explain_hash or args.dump_all:
            print(f"Explained hash for {name}:")
            explain_logic_hash(tree)
            print("Explain_expr_tree:")
            print(explain_expr_tree(tree))

        if args.pretty_print or args.dump_all:
            print(f"Pretty-print for {name}:")
            print(pretty_print(tree))

            if isinstance(tree, LogicOp):
                balanced_tree = balanced_tree_reduce(tree.op, tree.children)
            else:
                balanced_tree = tree
            dot = to_dot(balanced_tree)
            dot.render("./output/dotpath.dot", format="png", cleanup=True)

        if args.to_sympy or args.dump_all:
            print(f"Sympy expression for {name}: {to_sympy_expr(tree)}")

        if args.show_sympy or args.dump_all:
            sym_expr = to_sympy_expr(tree)
            print(f"\nSympy expression for {name}: {sym_expr}")
            try:
                from sympy import simplify_logic
                simplified = simplify_logic(sym_expr, form="dnf")
                print(f"Simplified Sympy logic: {simplified}")
            except Exception as e:
                print(f"Warning: Could not simplify expression: {e}")

        if args.to_ascii or args.dump_all:
            print(f"ASCII Tree for {name}:")
            print(logic_tree_to_ascii(tree))
            print("to_ascii():")
            print(to_ascii(tree))

        if args.to_svg:
            to_svg(tree)

        if args.to_png:
            if isinstance(tree, LogicOp):
                balanced_tree = balanced_tree_reduce(tree.op, tree.children)
            else:
                balanced_tree = tree
            to_png(balanced_tree)

        if args.save_golden:
            write_golden_file(name, tree)

        if args.check_golden:
            from utils_cli import check_against_golden
            check_against_golden(name, tree)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="SystemVerilog source file")
    parser.add_argument("--hash_tree", action="store_true", help="Print logic hash of each signal")
    parser.add_argument("--explain_hash", action="store_true", help="Explain hash derivation")
    parser.add_argument("--pretty_print", action="store_true", help="Pretty-print LogicTree")
    parser.add_argument("--to_sympy", action="store_true", help="Convert to Sympy expression")
    parser.add_argument("--to_ascii", action="store_true", help="ASCII tree print")
    parser.add_argument("--to_svg", action="store_true", help="Export LogicTree to SVG")
    parser.add_argument("--to_png", action="store_true", help="Export LogicTree to PNG")
    parser.add_argument("--save_golden", action="store_true", help="Save golden output file")
    parser.add_argument("--check_golden", action="store_true", help="Compare result to golden file")
    parser.add_argument("--dump_all", action="store_true", help="Dump all available representations")
    parser.add_argument("--case_to_if", action="store_true", help="Lower case statements to if-trees")
    parser.add_argument("--if_to_mux", action="store_true", help="Lower if-trees to mux-tree")
    parser.add_argument("--debug_log", action="store_true", help="Enable debug logging")
    parser.add_argument("-log", 
                        "--loglevel", default="warning", help="Provide loging level. Example --loglevel debug, default=warning")
    parser.add_argument("--show_sympy", action="store_true", help="Show Sympy expression logic")
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel.upper())

    ast = parse_sv_file(args.filename)
    signal_map = lower_sv_ast_to_signal_map(ast)

    # Optional lowering transformations
    if args.case_to_if:
        from logictree.transforms import case_to_if_tree
        #signal_map = {k: case_to_if_tree(v) for k, v in signal_map.items()}
        case_to_if_tree(signal_map)

    if args.if_to_mux:
        from logictree.transforms import if_tree_to_mux_tree
        signal_map = {k: if_tree_to_mux_tree(v) for k, v in signal_map.items()}
    
    handle_output(signal_map, args)

if __name__ == "__main__":
    main()
