import argparse
from antlr4 import FileStream, CommonTokenStream
from sv_parser.SystemVerilogSubsetLexer import SystemVerilogSubsetLexer
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser
from sv_parser.visitor import ASTBuilder
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from logictree.nodes import repair_tree_inputs, gate_summary
from utils.ascii_tree import logic_tree_to_ascii
from utils.graphviz_export import logic_tree_to_dot, save_dot_svg_png
#from scripts.to_dot_util import to_dot
from pprint import pprint
import logging
log = logging.getLogger(__name__)

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

    args = parser.parse_args()
    if args.debug_log:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s:%(name)s: %(message)s")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s")

    if args.analyze:
        analyze_file(args.analyze, args)
    else:
        parser.print_help()

    #if args.verilog:
    #    print(f"[stub] would emit Verilog for {args.verilog}")
    #if args.png:
    #    print(f"[stub] to_png")
    #    #to_png(args.png)


if __name__ == "__main__":
    main()
