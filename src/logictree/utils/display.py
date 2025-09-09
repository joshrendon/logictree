from sympy import symbols, Piecewise, S
import sympy as sympy
import graphviz
import re
from sympy.logic.boolalg import BooleanFalse, BooleanTrue
from rich.console import Console
from rich.text import Text
from sympy.logic.boolalg import And, Not, Or
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp, XorOp, XnorOp, NandOp
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.selects import BitSelect, PartSelect, Concat


def pretty_print(tree, indent=0):
    spacer = "  " * indent
    label = tree.__class__.__name__

    if isinstance(tree, NotOp):
        op_str = f"{spacer}NOT"
        children_str = pretty_print(tree.operand, indent + 1)
        return f"{op_str}\n{children_str}"
    elif isinstance(tree, LogicOp):
        op_str = f"{spacer}{tree.op}"
        children_str = "\n".join(
            pretty_print(child, indent + 1) for child in tree.children
        )
        return f"{op_str}\n{children_str}"
    elif isinstance(tree, EqOp):
        return f"{spacer} {tree.pretty_label()}"
    elif isinstance(tree, NeqOp):
        return f"{spacer} {tree.pretty_label()}"
    elif isinstance(tree, CaseStatement):
        lines = [f"{spacer}CASE("]
        lines.append(pretty_print(tree.selector, indent + 1))
        for item in tree.items:
            lines.append(pretty_print(item, indent + 1))
        lines.append(f"{spacer}")
        return "\n".join(lines)
    elif isinstance(tree, CaseItem):
        lines = [f"{spacer}CASE_ITEM:"]
        for label in tree.labels:
            lines.append(f"{spacer} label: {pretty_print(label, indent+2)}")
        lines.append(f"{spacer} body:")
        lines.append(pretty_print(tree.body, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, IfStatement):
        lines = [f"{spacer}IF:"]
        lines.append(f"{spacer} condition:")
        #lines.append(pretty_print(tree.cond, indent + 1))
        label = tree.cond.pretty_label() if hasattr(tree.cond, 'pretty_label') else tree.cond.label()
        space = " " * 3
        lines.append(f"{space} {label}")
        #lines.append(pretty_print(label, indent+ 2))
        lines.append(f"{spacer} then_branch:")
        lines.append(pretty_print(tree.then_branch, indent + 2))
        lines.append(f"{spacer} else_branch")
        lines.append(pretty_print(tree.else_branch, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, LogicMux):
        lines = [f"{spacer}LogicMux:"]
        lines.append(f"{spacer} selector:")
        #label = tree.selector.pretty_label() if hasattr(tree.selector, 'pretty_label') else tree.selector.label()
        #lines.append(f"{spacer} {label}")
        lines.append(pretty_print(tree.selector, indent + 2))
        lines.append(f"{spacer} if_true:")
        lines.append(pretty_print(tree.if_true, indent + 2))
        lines.append(f"{spacer} if_false:")
        lines.append(pretty_print(tree.if_false, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, LogicAssign):
        return f"{spacer}ASSIGN:\n{spacer}  {tree.lhs} = {pretty_print(tree.rhs, indent + 2)}"
    elif isinstance(tree, LogicVar):
        # return f"{spacer}VAR({tree.name})"
        return f"{spacer}{tree.name}"
    elif isinstance(tree, BitSelect):
        lines = [f"{spacer}BitSelect:"]
        lines.append(f"{spacer} {tree.label()}")
        return "\n".join(lines)
    elif isinstance(tree, LogicConst):
        # logic_val = "TRUE" if tree.value == 1 else "FALSE"
        logic_val = "FALSE"
        val = getattr(tree, "value", None)
        if val is not None:
            logic_val = val
        return f"{spacer}{logic_val}"
    elif isinstance(tree, LogicHole):
        return f"{spacer}HOLE({tree.name})"
    elif isinstance(tree, EmptyBranch):
        return f"{spacer}EmptyBranch"
    else:
        return f"{spacer}UNKNOWN<{type(tree).__name__}>: {str(tree)}"


def _pretty_print_expr(expr_str):
    console = Console()
    tokens = re.findall(r"[\w\[\]]+|[~&|()!^]", expr_str)
    styled = Text()
    for token in tokens:
        if token in {"&", "|", "~", "!", "^"}:
            styled.append(token, style="bold magenta")
        elif token in {"(", ")"}:
            styled.append(token, style="dim white")
        elif re.match(r"^[A-Za-z_]\w*$", token) or re.match(r"^\w+\[\d+\]$", token):
            styled.append(token, style="cyan")
        else:
            styled.append(token, style="white")
        styled.append(" ")
    console.print(styled)


def pretty_inline(tree):
    """
    Compact single-line representation: OP{child1, child2, ...}
    """
    if isinstance(tree, LogicOp):
        child_strs = [pretty_inline(child) for child in tree.children]
        # return f"{tree.op} {{', '.join(child_strs)}}"
        return f"{tree.op}{{{', '.join(child_strs)}}}"
    elif isinstance(tree, LogicVar):
        return tree.name
    elif isinstance(tree, LogicConst):
        return str(tree.value)
    else:
        return tree.default_label()

def to_dot(tree, g=None, parent=None, node_id_gen=[0]):
    if g is None:
        g = graphviz.Digraph()

    my_id = f"n{node_id_gen[0]}"
    node_id_gen[0] += 1

    label = ""
    if isinstance(tree, str):
        raise TypeError("Expected LogicTreeNode got str")
    if isinstance(tree, LogicOp):
        label = tree.op
    elif isinstance(tree, LogicVar):
        label = tree.name
    elif isinstance(tree, LogicConst):
        label = str(tree.value)
    elif isinstance(tree, LogicHole):
        label = f"?{tree.name}"
    else:
        label = "UNKNOWN"

    g.node(my_id, label)
    if parent:
        g.edge(parent, my_id)

    if isinstance(tree, LogicOp):
        for child in tree.children:
            to_dot(child, g, my_id, node_id_gen)

    return g

def to_symbolic_expr_str(node):
    if isinstance(node, LogicVar) or isinstance(node, LogicHole):
        return node.name
    elif isinstance(node, LogicConst):
        return "1" if node.value else "0"
    elif isinstance(node, LogicOp):
        op = node.op
        args = [to_symbolic_expr_str(child) for child in node.children]
        if op == "NOT":
            return f"~({args[0]})"
        elif op in {"AND", "OR", "XOR", "XNOR"}:
            symbol = {"AND": "&", "OR": "|", "XOR": "^", "XNOR": "~^"}[op]
            return f"({f' {symbol} '.join(args)})"
        else:
            return f"{op}({', '.join(args)})"
    else:
        return "<?>"

def to_sympy_expr(tree):
    if isinstance(tree, LogicVar):
        return symbols(tree.name)
    elif isinstance(tree, LogicConst):
        return int(tree.value)
    elif isinstance(tree, EmptyBranch):
        # Treat as 0 (False) for equivalence checking
        return S.false
    elif isinstance(tree, AndOp):
        return to_sympy_expr(tree.operands[0]) & to_sympy_expr(tree.operands[1])
    elif isinstance(tree, OrOp):
        return to_sympy_expr(tree.operands[0]) | to_sympy_expr(tree.operands[1])
    elif isinstance(tree, NotOp):
        return not(to_sympy_expr(tree.operand))
    elif isinstance(tree, EqOp):
        return to_sympy_expr(tree.lhs) == to_sympy_expr(tree.rhs)
    elif isinstance(tree, IfStatement):
        return Piecewise(
            (to_sympy_expr(tree.then_branch), to_sympy_expr(tree.cond)),
            (to_sympy_expr(tree.else_branch), True)
        )
    elif isinstance(tree, LogicMux):
        sel = to_sympy_expr(tree.selector)
        if_true = to_sympy_expr(tree.if_true)
        if_false = to_sympy_expr(tree.if_false)
        return Piecewise((if_true, sel), (if_false, True))
    elif isinstance(tree, BitSelect):
        # Treat like a variable with subscript notation: sel[0] becomes Symbol("sel_0")
        var = to_sympy_expr(tree.base)
        idx = to_sympy_expr(tree.index)
        return symbols(f"{var}_{idx}")
    elif isinstance(tree, PartSelect):
        var = to_sympy_expr(tree.base)
        msb = to_sympy_expr(tree.msb)
        lsb = to_sympy_expr(tree.lsb)
        return symbols(f"{var}_{msb}_{lsb}")
    elif isinstance(tree, Concat):
        parts = [to_sympy_expr(p) for p in tree.parts]
        return sum(p << (i * len(bin(p))-2) for i, p in enumerate(reversed(parts)))
    elif isinstance(tree, LogicAssign):
        return to_sympy_expr(tree.rhs)
    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")

def explain_expr_tree(tree):
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar

    if isinstance(tree, LogicOp):
        if tree.op == "MUX":
            cond, a, b = tree.children
            return f"({explain_expr_tree(cond)} ? {explain_expr_tree(a)} : {explain_expr_tree(b)})"
        elif tree.op == "XNOR":
            a, b = tree.children
            return f"({explain_expr_tree(a)} == {explain_expr_tree(b)})"
        elif tree.op == "AND":
            return " & ".join(f"({explain_expr_tree(c)})" for c in tree.children)
        elif tree.op == "OR":
            return " | ".join(f"({explain_expr_tree(c)})" for c in tree.children)
        elif tree.op == "NOT":
            return f"(~{explain_expr_tree(tree.children[0])})"
        else:
            return (
                f"{tree.op}({', '.join(explain_expr_tree(c) for c in tree.children)})"
            )
    elif isinstance(tree, LogicVar):
        return tree.name
    elif isinstance(tree, LogicConst):
        return "1" if tree.value else "0"
    else:
        return f"{tree}"

def multi_branch_mux_pretty_print(node: LogicMux, indent: int = 2) -> str:
    """
    Flatten a nested LogicMux chain into a human-readable switch-like table.
    Assumes the tree is structurally valid and was lowered from a case/if chain.
    """
    if not isinstance(node, LogicMux):
        raise TypeError(f"Expected LogicMux node, got {type(node)}")

    entries = []

    def walk_mux(n):
        if not isinstance(n, LogicMux):
            entries.append(("default", n))
            return

        cond = n.selector
        true_branch = n.if_true
        false_branch = n.if_false

        entries.append((cond, true_branch))
        walk_mux(false_branch)

    walk_mux(node)

    # Build formatted table
    pad = " " * indent
    lines = ["MUX Table:", f"{pad}Condition     | Output", f"{pad}{'-'*14}-+-{'-'*20}"]
    for cond, out in entries:
        cond_str = str(cond) if cond != "default" else "default"
        out_str = str(out) if not isinstance(out, EmptyBranch) else "<empty>"
        lines.append(f"{pad}{cond_str:<14} | {out_str}")

    return "\n".join(lines)
