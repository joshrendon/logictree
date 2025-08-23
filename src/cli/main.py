import argparse
import logging

from logictree.nodes import ops
from logictree.pipeline import lower_sv_file_to_logic
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.if_to_mux import if_tree_to_mux_tree
from logictree.transforms.signal_resolution import resolve_signal_vars
from logictree.utils.analysis import explain_logic_hash, get_logic_hash
from logictree.utils.display import (
    explain_expr_tree,
    pretty_print,
    to_dot,
    to_sympy_expr,
)
from logictree.utils.reduce import balanced_tree_reduce
from utils.ascii_tree import logic_tree_to_ascii, to_ascii
from utils.utils_cli import write_golden_file

log = logging.getLogger(__name__)

MODULE_NAME = ""

def handle_output(signal_map, args):
    for name, tree in signal_map.items():
        if args.hash_tree or args.dump_all:
            print(f"DEBUG: name: {name}")
            print(f"Hash for {name}: {get_logic_hash(tree)}")

        if args.explain_hash or args.dump_all:
            print(f"Explained hash for {name}:")
            explain_logic_hash(tree)
            print("Explain_expr_tree:")
            print(explain_expr_tree(tree))

        if args.pretty_print or args.dump_all:
            print(f"Pretty-print for {name}:")
            print(pretty_print(tree))
            balanced_tree = (
                balanced_tree_reduce(tree.op, tree.children)
                if isinstance(tree, ops.LogicOp)
                else tree
            )
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
            from logictree.graphviz_utils import to_svg

            to_svg(tree)

        if args.to_png:
            from logictree.graphviz_utils import to_png

            balanced_tree = (
                balanced_tree_reduce(tree.op, tree.children)
                if isinstance(tree, ops.LogicOp)
                else tree
            )
            to_png(balanced_tree)

        if args.save_golden:
            write_golden_file(name, tree)

        if args.check_golden:
            from utils_cli import check_against_golden

            check_against_golden(name, tree)


def build_parser():
    parser = argparse.ArgumentParser(description="LogicTree CLI Tool")
    parser.add_argument("filename", help="SystemVerilog source file")

    # Output Options
    out = parser.add_argument_group("Output Options")
    out.add_argument("--hash_tree", action="store_true", help="Print logic hash of each signal")
    out.add_argument("--explain_hash", action="store_true", help="Explain hash derivation")
    out.add_argument("--pretty_print", action="store_true", help="Pretty-print LogicTree")
    out.add_argument("--to_sympy", action="store_true", help="Convert to Sympy expression")
    out.add_argument("--show_sympy", action="store_true", help="Show Sympy expression logic")
    out.add_argument("--to_ascii", action="store_true", help="ASCII tree print")
    out.add_argument("--to_svg", action="store_true", help="Export LogicTree to SVG")
    out.add_argument("--to_png", action="store_true", help="Export LogicTree to PNG")
    out.add_argument("--save_golden", action="store_true", help="Save golden output file")
    out.add_argument("--check_golden", action="store_true", help="Compare result to golden file")
    out.add_argument("--dump_all", action="store_true", help="Dump all available representations")
    out.add_argument("--explore", action="store_true", help="Launch GUI to explore LogicTree")

    # Lowering Options
    lower = parser.add_argument_group("Lowering Options")
    lower.add_argument("--case_to_if", action="store_true", help="Lower case statements to if-trees")
    lower.add_argument("--if_to_mux", action="store_true", help="Lower if-trees to mux-tree")
    lower.add_argument("--to_primitives", action="store_true", help="Lower to primitive gates {AND, OR, NOT}")

    # Logging
    parser.add_argument(
        "--loglevel",
        default="warning",
        choices=["debug", "info", "warning", "error"],
        help="Set log level (default: warning)",
    )

    return parser

def apply_lowering(signal_map, args):
    lowered = {}
    for name, tree in signal_map.items():
        import logictree.nodes.control.case as control
        if args.case_to_if and isinstance(tree, control.CaseStatement):
            tree = case_to_if_tree(tree)
        if args.if_to_mux and isinstance(tree, control.IfStatement):
            tree = if_tree_to_mux_tree(tree)
        if args.to_primitives and hasattr(tree, "to_primitives"):
            tree = tree.to_primitives()
        lowered[name] = tree
    return lowered


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))

    lowerer = SVToLogicTreeLowerer()
    signal_map = lower_sv_file_to_logic(args.filename)
    lowered_map = apply_lowering(signal_map, args)
    resolved_map = {
        name: resolve_signal_vars(tree, lowerer.signal_map)
        for name, tree in lowered_map.items()
    }

    global MODULE_NAME
    MODULE_NAME = lowerer.module_name

    if args.explore:
        from gui.explorer_server import launch_explorer
        from logictree.utils.display import pretty_inline
        
        for name, tree in resolved_map.items():
            tree.set_viz_label(f"{name} = {pretty_inline(tree)}")
            launch_explorer(logic_tree_original=tree, tree_name_input=name)
        return

    log.debug(f"resolved_map: {resolved_map}")
    handle_output(resolved_map, args)


if __name__ == "__main__":
    main()
