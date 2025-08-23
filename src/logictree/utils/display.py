import re

import sympy as sympy
from rich.console import Console
from rich.text import Text
from sympy.logic.boolalg import And, Not, Or

import graphviz


def pretty_print(tree, indent=0):
    spacer = "  " * indent
    label = tree.__class__.__name__

    from logictree.nodes.control import CaseItem, CaseStatement, IfStatement, LogicAssign
    from logictree.nodes.hole.hole import LogicHole
    from logictree.nodes.ops.gates import NotOp
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar

    if isinstance(tree, NotOp):
        op_str = f"{spacer}NOT"
        children_str = pretty_print(tree.operand, indent + 1)
        return f"{op_str}\n{children_str}"
    elif isinstance(tree, LogicOp):
        op_str = f"{spacer}{tree.op}"
        children_str = "\n".join(pretty_print(child, indent + 1) for child in tree.children)
        return f"{op_str}\n{children_str}"
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
        lines.append(pretty_print(tree.condition, indent + 1))
        lines.append(f"{spacer} then_body:")
        lines.append(pretty_print(tree.then_body, indent + 2))
        lines.append(f"{spacer} else_body:")
        lines.append(pretty_print(tree.else_body, indent + 2))
        return "\n".join(lines)
    elif isinstance(tree, LogicAssign):
         return f"{spacer}ASSIGN:\n{spacer}  {tree.lhs} = {pretty_print(tree.rhs, indent + 2)}"
    elif isinstance(tree, LogicVar):
        #return f"{spacer}VAR({tree.name})"
        return f"{spacer}{tree.name}"
    elif isinstance(tree, LogicConst):
        #logic_val = "TRUE" if tree.value == 1 else "FALSE"
        logic_val = "FALSE"
        val = getattr(tree, "value", None)
        if val is not None:
            logic_val = val
        return f"{spacer}{logic_val}"
    elif isinstance(tree, LogicHole):
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

def pretty_inline(tree):
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
    """
    Compact single-line representation: OP{child1, child2, ...}
    """
    if isinstance(tree, LogicOp):
        child_strs = [pretty_inline(child) for child in tree.children]
        #return f"{tree.op} {{', '.join(child_strs)}}"
        return f"{tree.op}{{{', '.join(child_strs)}}}"
    elif isinstance(tree, LogicVar):
        return tree.name
    elif isinstance(tree, LogicConst):
        return str(tree.value)
    else:
        return tree.default_label()

def to_dot(tree, g=None, parent=None, node_id_gen=[0]):
    from logictree.nodes.hole.hole import LogicHole
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
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
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
    from logictree.nodes.hole.hole import LogicHole
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
        return "<?>"

from sympy.logic.boolalg import BooleanFalse, BooleanTrue


def to_sympy_expr(tree):
    from logictree.nodes.hole.hole import LogicHole
    from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
    if isinstance(tree, LogicConst):
        val = int(tree.value)
        if val == 0:
            return BooleanFalse()
        elif val == 1:
            return BooleanTrue()
    elif isinstance(tree, LogicVar):
        return sympy.Symbol(tree.name)

    elif isinstance(tree, LogicHole):
        return sympy.Symbol(tree.name)  # treat holes as symbolic vars too

    elif isinstance(tree, LogicOp):
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
            return f"{tree.op}({', '.join(explain_expr_tree(c) for c in tree.children)})"
    elif isinstance(tree, LogicVar):
        return tree.name
    elif isinstance(tree, LogicConst):
        return "1" if tree.value else "0"
    else:
        return f"{tree}"

