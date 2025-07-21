import argparse
from antlr4 import FileStream, CommonTokenStream
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from logictree.nodes import repair_tree_inputs, gate_summary
from logictree.utils import get_logic_hash, explain_logic_hash, to_sympy_expr
from utils.ascii_tree import logic_tree_to_ascii
from utils.graphviz_export import logic_tree_to_dot, save_dot_svg_png
from utils.utils_cli import write_golden_file
from pprint import pprint
import logging

log = logging.getLogger(__name__)


def parse_sv_to_logic_tree(path, args):
    print(f"\nAnalyzing: {path}")
    #from scripts.parse_sv import parse_sv_file
    input_stream = FileStream(path)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    tree = parser.compilation_unit()

    ast = ASTBuilder().visit(tree)
    logic_tree_lowerer = SVToLogicTreeLowerer()
    tree = logic_tree_lowerer.lower_file(path)

    if args.to_png:
        tree.to_png("logic_tree.png")
    if args.to_svg:
        tree.to_svg("logic_tree.svg")
    if args.to_dot:
        tree.to_dot("logic_tree.dot")

    return tree

def analyze_file(path, args):
    print(f"\nAnalyzing: {path}")
    #from scripts.parse_sv import parse_sv_file
    input_stream = FileStream(path)
    lexer = SystemVerilogSubsetLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = SystemVerilogSubsetParser(tokens)
    tree = parser.compilation_unit()

    ast = ASTBuilder().visit(tree)
    logic_tree_lowerer = SVToLogicTreeLowerer()

    for module in ast['modules']:
        for item in module['items']:
            if item['type'] == 'assign':
                signal, logic = logic_tree_lowerer.visitAssign_statement(item['ctx'])

                repair_tree_inputs(logic)

                print(f"\nSignal: {signal}")
                log.debug("Full LogicTree: %s", logic)
                print("ASCII Tree:\n" + logic_tree_to_ascii(logic))
                logic_tree_to_dot(logic, signal)

                if args.to_dot or args.to_png or args.to_svg:
                    dot_str = logic_tree_to_dot(logic, signal_name=signal)
                    if args.to_dot:
                        Path(f"{signal_name}.dot").write_text(dot_str)
                    if args.to_png or args.to_svg:
                        save_dot_svg_png(dot_str, f"{signal}_tree")

                print(f"  Verilog: {logic.to_verilog()}")
                print(f"  Depth:   {logic.depth()}")
                print(f"  Gates:   {gate_summary(logic)}")

def main():
    parser = argparse.ArgumentParser(description="SV AST + LogicTree Tool")
    #parser.add_argument('--verilog', help='Emit Verilog from symbolic IR')
    #parser.add_argument('--png',     help='Output the logicTree as graphViz png') # just a flag, uses default output file <output.png>
    parser.add_argument(
        "--analyze", type=str, metavar="FILE",
        help="Analyze an Parse a SystemVerilog file"
    )
    parser.add_argument(
        "--debug-log", action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument("--to_dot", action="store_true", help="Output AST Graph as a Graphviz dotfile")
    parser.add_argument("--to_png", action="store_true", help="Output AST Graph a png")
    parser.add_argument("--to_svg", action="store_true", help="Output AST Graph a svg")

    parser.add_argument('--hash_tree', help='Get SHA256 hash of the logic tree from a SystemVerilog file')
    parser.add_argument('--explain_hash', help='Print canonical logic expression and hash with rich syntax highlighting')
    parser.add_argument('--dump_bdd_order', help='Dump sorted input variables and BDD internal order for a tree')
    parser.add_argument('--sympy_expr', help='Print Sympy-form Boolean expression of the logic tree')
    
    parser.add_argument('--save_golden', type=str, help="Save golden hash + inputs + expression to golden_hashes/<name>.json")

    args = parser.parse_args()
    if args.debug_log:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s:%(name)s: %(message)s")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s")

    if args.hash_tree:
        tree = parse_sv_to_logic_tree(args.hash_tree, args)
        print("Inputs (raw):", tree.inputs)
        print("Inputs (sorted):", sorted(tree.inputs()))
        logic_hash, expr_str = get_logic_hash(tree, return_expr=True)
        print("Logic SHA256 Hash:\n", logic_hash)
        
        if args.save_golden:
            golden_path = f"golden_hashes/{args.save_golden}.json"
            inputs_flat = sorted(tree.inputs()) if callable(tree.inputs()) else sorted(tree.inputs())
            write_golden_file(golden_path, name=args.save_golden, logic_hash=logic_hash,
                              expr_str=expr_str, inputs_flat=inputs_flat, inputs_decl=[])
            print(f"Golden Hash written to: {golden_path}")

    elif args.explain_hash:
        tree = parse_sv_to_logictree(args.explain_hash)
        explain_logic_hash(tree)

    elif args.dump_bdd_order:
        tree = parse_sv_to_logictree(args.dump_bdd_order)
        inputs = sorted(tree.inputs())
        print("Sorted Input Variables:")
        for i, name in enumerate(inputs):
            print(f"{i}: {name}")
        bdd = _bdd.BDD()
        for var in inputs:
            bdd.declare(var)
        print("\nBDD Internal Variable Order:")
        print(list(bdd.vars))
    
    elif args.sympy_expr:
        tree = parse_sv_to_logictree(args.sympy_expr)
        print("Sympy Boolean Expression:\n", to_sympy_expr(tree))

    elif args.analyze:
        analyze_file(args.analyze, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
