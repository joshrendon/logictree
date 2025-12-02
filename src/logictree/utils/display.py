import logging
import re

import sympy as sympy
from rich.console import Console
from rich.text import Text

import graphviz
from logictree.nodes.control.alwaysblock import AlwaysBlock
from logictree.nodes.control.assign import ContinuousAssign, LogicAssign, ProceduralAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect
from logictree.nodes.struct.module import Module
from logictree.nodes.struct.statement import BlockStatement

log = logging.getLogger(__name__)


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
    elif isinstance(tree, Module):
        lines = [f"{spacer}Module {tree.name}:"]
        if tree.ports:
            lines.append(f"{spacer}  Ports: {', '.join(tree.ports)}")

        if tree.signal_map:
            lines.append(f"{spacer}  Signals:")
            for name, sig in tree.signal_map.items():
                lines.append(f"{spacer}    {name}: {sig}")

        if tree.assignments:
            lines.append(f"{spacer}  Assignments:")
            for name, a in tree.assignments.items():
                lines.append(f"{spacer}    {name} = {pretty_print(a.rhs, indent+2)}")

        if tree.always_blocks:
            lines.append(f"{spacer}  Always Blocks:")
            for ab in tree.always_blocks:
                lines.append(pretty_print(ab, indent+2))

        if tree.instances:
            lines.append(f"{spacer}  Instances: {tree.instances}")

        return "\n".join(lines)
    elif isinstance(tree, AlwaysBlock):
        kind = getattr(tree, "kind", "unknown")
        label = getattr(tree, "label", None)
        header = f"{spacer}Always {kind}" + (f" : {label}" if label else "")
        body = pretty_print(tree.body, indent+1) if tree.body else f"{spacer}  <empty>"
        return f"{header}\n{body}"
    elif isinstance(tree, BlockStatement):
        lines = [f"{spacer}Block:"]
        for stmt in tree.statements:
            lines.append(pretty_print(stmt, indent+1))
        return "\n".join(lines)
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
    elif isinstance(tree, ITEOp):
        lines = [f"{spacer}ITEOp:"]
        lines.append(f"{spacer} cond:")
        lines.append(pretty_print(tree.cond, indent + 2))
        lines.append(f"{spacer} if_true:")
        lines.append(pretty_print(tree.if_true, indent + 2))
        lines.append(f"{spacer} if_false:")
        lines.append(pretty_print(tree.if_false, indent + 2))
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
    elif isinstance(tree, ContinuousAssign):
        return f"CONT_ASSIGN: {tree.pretty_inline()}"
    elif isinstance(tree, ProceduralAssign):
        arrow = "=" if tree.blocking else "<="
        return f"PROC_ASSIGN: {tree.lhs.pretty_inline()} {arrow} {pretty_print(tree.rhs)}"
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
    elif isinstance(tree, BlockStatement):
        return f"{spacer}BlockStatement{pretty_print(tree.statements)}"
    elif isinstance(tree, tuple):
        return f"{spacer}tuple<{type(tree).__name__}>: {str(tree)}"
    elif isinstance(tree, list):
        return f"{spacer}LIST<{type(tree).__name__}>: {str(tree)}"
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
    Compact single-line representation for any LogicTree structure.
    Handles multi-bit results (lists of nodes) as well.
    """
    from logictree.nodes.control.assign import LogicAssign
    from logictree.nodes.control.case import CaseItem, CaseStatement
    from logictree.nodes.control.ifstatement import IfStatement
    from logictree.nodes.ops.ite import ITEOp
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar

    if isinstance(tree, LogicOp):
        child_strs = [pretty_inline(child) for child in tree.children]
        return f"{tree.op}{{{', '.join(child_strs)}}}"
    elif isinstance(tree, LogicVar):
        return tree.name
    elif isinstance(tree, LogicConst):
        return f"{tree.width}'d{tree.value}" if tree.width and tree.width > 1 else str(tree.value)
    elif isinstance(tree, BlockStatement):
        return f"BlockStatement({pretty_inline(tree.statements)})"
    elif isinstance(tree, ITEOp):
        return f"ITE({pretty_inline(tree.cond)}, {pretty_inline(tree.if_true)}, {pretty_inline(tree.if_false)})"
    elif isinstance(tree, IfStatement):
        return f"If({pretty_inline(tree.cond)})[{pretty_inline(tree.then_branch)}]else[{pretty_inline(tree.else_branch)}]"
    elif isinstance(tree, CaseStatement):
        items_str = "; ".join(pretty_inline(item) for item in tree.items)
        default_str = f"default:{pretty_inline(tree.default)}" if tree.default else ""
        return f"Case({pretty_inline(tree.selector)})[{items_str}{default_str}]"
    elif isinstance(tree, CaseItem):
        labels = ", ".join(pretty_inline(lbl) for lbl in tree.labels)
        return f"Item({labels} => {pretty_inline(tree.body)})"
    elif isinstance(tree, LogicAssign):
        return f"{pretty_inline(tree.lhs)}={pretty_inline(tree.rhs)}"
    elif isinstance(tree, EmptyBranch):
        return "EmptyBranch"
    elif isinstance(tree, list):
        return "[" + ", ".join(pretty_inline(x) for x in tree) + "]"
    else:
        # fallback: use node’s default label if it has one
        if hasattr(tree, "default_label"):
            return tree.default_label()
        return f"UNKNOWN<{type(tree).__name__}>"


def to_dot(tree, g=None, parent=None, node_id_gen=[0]):
    """
    Recursively render a LogicTreeNode into a Graphviz Digraph.
    If called at the top level (g=None), returns the Digraph object.
    Otherwise, returns the node id string.
    """
    top_level = g is None
    if g is None:
        g = graphviz.Digraph()
        g.attr("graph", colorscheme="set19")
        g.attr("node", style="filled", colorscheme="set19", fontname="monospace")

    my_id = f"n{node_id_gen[0]}"
    node_id_gen[0] += 1

    # --- label/shape selection ---
    #shape, fill = "ellipse", "white"
    shape, fill = "ellipse", "8"
    if isinstance(tree, str):
        raise TypeError("Expected LogicTreeNode got str")
    elif isinstance(tree, LogicVar):
        #label, shape, fill = tree.name, "ellipse", "lightblue"
        label, shape, fill = tree.name, "ellipse", "2"
    elif isinstance(tree, LogicConst):
        #label, shape, fill = str(tree.value), "ellipse", "lightgrey"
        label, shape, fill = str(tree.value), "ellipse", "9"
    elif isinstance(tree, AndOp):
        #label, shape, fill = tree.op, "box", "lightgreen"
        label, shape, fill = tree.op, "box", "3"
    elif isinstance(tree, OrOp):
        #label, shape, fill = tree.op, "box", "royalblue"
        label, shape, fill = tree.op, "box", "5"
    elif isinstance(tree, NotOp):
        #label, shape, fill = tree.op, "box", "tomato"
        label, shape, fill = tree.op, "box", "1"
    elif isinstance(tree, LogicHole):
        label, shape = f"?{tree.name}", "ellipse"
    elif isinstance(tree, LogicMux):
        label, shape = "Mux", "box"
    elif isinstance(tree, ITEOp):
        label = "{ ITE | { <cond> cond | <t> true | <f> false } }"
        shape = "record"
        fill = "4"
    elif isinstance(tree, LogicAssign):
        label, shape, fill = f"assign {tree.lhs.name}", "box", "4"
    elif isinstance(tree, ProceduralAssign):
        label, shape = f"proc {tree.lhs.name}", "box"
    elif isinstance(tree, ContinuousAssign):
        label, shape = f"cont {tree.lhs.name}", "box"
    elif isinstance(tree, LogicMux):
        label, shape, fill = "Mux", "diamond", "8"
    elif isinstance(tree, IfStatement):
        label, shape = "if", "diamond"
    elif isinstance(tree, CaseStatement):
        label, shape = "case", "diamond"
    elif isinstance(tree, CaseItem):
        label, shape = "case_item", "box"
    else:
        label, shape, fill = tree.__class__.__name__, "box", "8"

    #log.debug(f"label, shape, fillcolor: {label}, {shape}, {fill}")
    g.node(my_id, label, shape=shape, fillcolor=fill)
    if parent:
        g.edge(parent, my_id)

    # --- recurse by type ---
    if isinstance(tree, LogicMux):
        cond_id = to_dot(tree.selector, g, None, node_id_gen)
        t_id = to_dot(tree.if_true, g, None, node_id_gen)
        f_id = to_dot(tree.if_false, g, None, node_id_gen)
        g.edge(my_id, cond_id, label="cond")
        g.edge(my_id, t_id, label="true")
        g.edge(my_id, f_id, label="false")

    elif isinstance(tree, ITEOp):
        cond_id = to_dot(tree.cond, g, None, node_id_gen)
        t_id = to_dot(tree.if_true, g, None, node_id_gen)
        f_id = to_dot(tree.if_false, g, None, node_id_gen)
        g.edge(f"{my_id}:cond", cond_id)
        g.edge(f"{my_id}:t", t_id)
        g.edge(f"{my_id}:f", f_id)
    elif isinstance(tree, LogicOp):
        for child in tree.children:
            child_id = to_dot(child, g, my_id, node_id_gen) # noqa: F841  # side-effect: populates digraph
            #g.edge(my_id, child_id)

    elif isinstance(tree, (LogicAssign, ProceduralAssign, ContinuousAssign)):
        _ = to_dot(tree.rhs, g, my_id, node_id_gen)

    elif isinstance(tree, IfStatement):
        cond_id = to_dot(tree.cond, g, my_id, node_id_gen)
        if tree.then_branch:
            then_id = to_dot(tree.then_branch, g, my_id, node_id_gen)
            g.edge(my_id, then_id, label="then")
        if tree.else_branch:
            else_id = to_dot(tree.else_branch, g, my_id, node_id_gen)
            g.edge(my_id, else_id, label="else")

    elif isinstance(tree, CaseStatement):
        sel_id = to_dot(tree.selector, g, my_id, node_id_gen) # noqa: F841  # side-effect: populates digraph
        for item in tree.items:
            item_id = to_dot(item, g, my_id, node_id_gen)
            g.edge(my_id, item_id)
        if tree.default is not None:
            def_id = to_dot(tree.default, g, my_id, node_id_gen)
            g.edge(my_id, def_id, label="default")

    elif isinstance(tree, CaseItem):
        labels_id = to_dot(tree.labels, g, my_id, node_id_gen)
        body_id = to_dot(tree.body, g, my_id, node_id_gen)
        g.edge(my_id, labels_id, label="labels")
        g.edge(my_id, body_id, label="body")

    return g if top_level else my_id

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
