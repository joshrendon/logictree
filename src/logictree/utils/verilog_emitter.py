from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.utils.formatting import pretty_expr


def mux_chain_to_verilog_expr(mux: LogicMux) -> str:
    """
    Convert a multi-branch LogicMux tree into a Verilog-style ternary expression.

    Example output:
        (sel == 1'd0) ? a : (sel == 1'd1) ? b : /* empty */
    """

    def emit_expr(node: LogicTreeNode) -> str:
        if isinstance(node, LogicMux):
            cond_str = pretty_expr(node.selector)
            true_branch = emit_expr(node.if_true)
            false_branch = emit_expr(node.if_false)
            return f"({cond_str}) ? {true_branch} : {false_branch}"

        elif isinstance(node, LogicVar):
            return node.name

        elif isinstance(node, LogicConst):
            return node.label()

        elif isinstance(node, EmptyBranch):
            return "/* empty */"

        else:
            return pretty_expr(node)

    return emit_expr(mux)
