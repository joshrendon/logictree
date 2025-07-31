from logictree.nodes import ops, control, base, hole
from logictree.utils.formating import indent
import hashlib
import itertools
import re
#from dd import autoref as _bdd
from dd.autoref import BDD
from sympy import symbols
from sympy import sympify
from sympy.logic.boolalg import And, Or, Not
import sympy as sympy
from rich.console import Console
from rich.text import Text
from typing import Dict, Tuple, Union, Optional
import graphviz

def pretty_print(tree, indent=0):
    spacer = "  " * indent
    label = tree.__class__.__name__

    from logictree.nodes.ops.gates import NotOp

    if isinstance(tree, NotOp):
        op_str = f"{spacer}NOT"
        children_str = pretty_print(tree.operand, indent + 1)
        return f"{op_str}\n{children_str}"
    elif isinstance(tree, ops.LogicOp):
        op_str = f"{spacer}{tree.op}"
        children_str = "\n".join(pretty_print(child, indent + 1) for child in tree.children)
        return f"{op_str}\n{children_str}"
    elif isinstance(tree, control.CaseStatement):
        lines = [f"{spacer}CASE("]
        lines.append(pretty_print(tree.selector, indent + 1))
        for item in tree.items:
            lines.append(pretty_print(item, indent + 1))
        lines.append(f"{spacer}")
        return "\n".join(lines)
    elif isinstance(tree, control.CaseItem):
        lines = [f"{spacer}CASE_ITEM:"]
        for label in tree.labels:
            lines.append(f"{spacer} label: {pretty_print(label, indent+2)}")
        lines.append(f"{spacer} body:")
        lines.append(pretty_print(tree.body, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, control.IfStatement):
        lines = [f"{spacer}IF:"]
        lines.append(f"{spacer} condition:")
        lines.append(pretty_print(tree.condition, indent + 1))
        lines.append(f"{spacer} then_body:")
        lines.append(pretty_print(tree.then_body, indent + 2))
        lines.append(f"{spacer} else_body:")
        lines.append(pretty_print(tree.else_body, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, control.LogicAssign):
         return f"{spacer}ASSIGN:\n{spacer}  {tree.lhs} = {pretty_print(tree.rhs, indent + 2)}"
    elif isinstance(tree, ops.LogicVar):
        #return f"{spacer}VAR({tree.name})"
        return f"{spacer}{tree.name}"
    elif isinstance(tree, ops.LogicConst):
        logic_val = "TRUE" if tree.value == 1 else "FALSE"
        return f"{spacer}{logic_val}"
    elif isinstance(tree, hole.LogicHole):
        return f"{spacer}HOLE({tree.name})"
    else:
        return f"{spacer}UNKNOWN<{type(tree).__name__}>: {str(tree)}"

def _pretty_print_expr(expr_str):
    console = Console()
    tokens = re.findall(r'[\w\[\]]+|[~&|()!^]', expr_str)
    styled = Text()
    for token in tokens:
        if token in {'&', '|', '~', '!', '^'}:
            styled.append(token, style="bold magenta")
        elif token in {'(', ')'}:
            styled.append(token, style="dim white")
        elif re.match(r'^[A-Za-z_]\w*$', token) or re.match(r'^\w+\[\d+\]$', token):
            styled.append(token, style="cyan")
        else:
            styled.append(token, style="white")
        styled.append(' ')
    console.print(styled)

def to_dot(tree, g=None, parent=None, node_id_gen=[0]):
    if g is None:
        g = graphviz.Digraph()

    my_id = f"n{node_id_gen[0]}"
    node_id_gen[0] += 1

    label = ""
    if isinstance(tree, str):
        raise TypeError("Expected base.LogicTreeNode got str")
    if isinstance(tree, ops.LogicOp):
        label = tree.op
    elif isinstance(tree, ops.LogicVar):
        label = tree.name
    elif isinstance(tree, ops.LogicConst):
        label = str(tree.value)
    elif isinstance(tree, hole.LogicHole):
        label = f"?{tree.name}"
    else:
        label = "UNKNOWN"

    g.node(my_id, label)
    if parent:
        g.edge(parent, my_id)

    if isinstance(tree, ops.LogicOp):
        for child in tree.children:
            to_dot(child, g, my_id, node_id_gen)

    return g

def to_symbolic_expr_str(node):
    if isinstance(node, ops.LogicVar) or isinstance(node, hole.LogicHole):
        return node.name
    elif isinstance(node, ops.LogicConst):
        return "1" if node.value else "0"
    elif isinstance(node, ops.LogicOp):
        op = node.op
        args = [to_symbolic_expr_str(child) for child in node.children]
        if op == "NOT":
            return f"~({args[0]})"
        elif op in {"AND", "OR", "XOR", "XNOR"}:
            symbol = {
                "AND": "&",
                "OR": "|",
                "XOR": "^",
                "XNOR": "~^"
            }[op]
            return f"({f' {symbol} '.join(args)})"
        else:
            return f"{op}({', '.join(args)})"
    else:
        return f"<?>"

from sympy.logic.boolalg import BooleanTrue, BooleanFalse
def to_sympy_expr(tree: base.LogicTreeNode):
    if isinstance(tree, ops.LogicConst):
        val = int(tree.value)
        #result = sympify(bool(val))
        #print(f"[SYM CONST] Interpreting ops.LogicConst({tree.value}) as {val} ({type(val)})")
        if val == 0:
            return BooleanFalse()
        elif val == 1:
            return BooleanTrue()
    elif isinstance(tree, ops.LogicVar):
        return sympy.Symbol(tree.name)

    elif isinstance(tree, hole.LogicHole):
        return sympy.Symbol(tree.name)  # treat holes as symbolic vars too

    elif isinstance(tree, ops.LogicOp):
        # Recursively convert children
        children = [to_sympy_expr(c) for c in tree.children]

        if tree.op == "AND":
            return And(*children)
        elif tree.op == "OR":
            return Or(*children)
        elif tree.op == "NOT":
            return Not(children[0])
        elif tree.op == "IF":
            cond, then_branch, else_branch = children
            return sympy.Piecewise((then_branch, cond), (else_branch, True))
        elif tree.op == "MUX":
            # MUX(cond, a, b) → (cond & a) | (~cond & b)
            cond_expr, a_expr, b_expr = children
            #print(f"[MUX DEBUG] cond_expr={cond_expr} ({type(cond_expr)}), a_expr={a_expr} ({type(a_expr)}), b_expr={b_expr} ({type(b_expr)})")
            return Or(And(cond_expr, a_expr), And(Not(cond_expr), b_expr))
        elif tree.op == "EQ":
            assert len(children) == 2
            return sympy.Eq(children[0], children[1])
        elif tree.op == "XNOR":
            a, b = children
            return a == b
        elif tree.op == "XOR":
            return sympy.Xor(*children)
        elif tree.op == "NAND":
            return Not(And(*children))
        elif tree.op == "NOR":
            return Not(Or(*children))
        else:
            raise NotImplementedError(f"Unsupported op: {tree.op}")
    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")

def explain_expr_tree(tree):
    if isinstance(tree, ops.LogicOp):
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
            return f"{tree.op}({', '.join(explain_expr_tree(c) for c in tree.children)})"
    elif isinstance(tree, ops.LogicVar):
        return tree.name
    elif isinstance(tree, ops.LogicConst):
        return "1" if tree.value else "0"
    else:
        return f"{tree}"

