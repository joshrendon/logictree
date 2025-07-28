from logictree.nodes import LogicOp, LogicVar, LogicConst, LogicHole, LogicNode, CaseStatement, CaseItem, IfStatement, LogicAssign
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

def balance_logic_tree(tree):
    if isinstance(tree, LogicOp):
        balanced_children = [balance_logic_tree(child) for child in tree.children]
        return balanced_tree_reduce(tree.op, balanced_children)
    return tree

def balanced_tree_reduce(op_name, inputs):
    """Builds a balanced binary tree of LogicOps over the inputs."""
    if not inputs:
        raise ValueError("Cannot reduce empty input list")

    if len(inputs) == 1:
        return inputs[0]

    # Build binary tree recursively
    mid = len(inputs) // 2
    left = balanced_tree_reduce(op_name, inputs[:mid])
    right = balanced_tree_reduce(op_name, inputs[mid:])
    return LogicOp(op_name, [left, right])

# === LOGICTREE COMPARISON ===
def compare_logic_trees(tree1, tree2, method='auto', debug=False):
    if method == 'structure':
        return _compare_structure(tree1, tree2)
    elif method == 'eval':
        return _compare_truth_table(tree1, tree2)
    elif method == 'bdd':
        return _compare_bdd(tree1, tree2)
    elif method == 'hash':
        return get_logic_hash(tree1) == get_logic_hash(tree2)
    elif method == 'auto':
        if _compare_structure(tree1, tree2):
            if debug: print("Structure matched.")
            return True
        if get_logic_hash(tree1) == get_logic_hash(tree2):
            if debug: print("Hash matched.")
            return True
        if _compare_bdd(tree1, tree2):
            if debug: print("BDD matched.")
            return True
        return False
    else:
        raise ValueError(f"Unknown comparison method: {method}")

def _compare_structure(t1, t2):
    if t1.op != t2.op or len(t1.children) != len(t2.children):
        return False
    return all(_compare_structure(c1, c2) for c1, c2 in zip(t1.children, t2.children))

def _compare_truth_table(t1, t2):
    inputs = sorted(set(t1.inputs()) | set(t2.inputs()))
    for assignment in itertools.product([False, True], repeat=len(inputs)):
        env = dict(zip(inputs, assignment))
        if t1.evaluate(env) != t2.evaluate(env):
            return False
    return True

def _compare_bdd(t1, t2):
    return to_bdd(t1) == to_bdd(t2)

# === BDD HASHING AND DEBUGGING ===
def get_logic_hash(tree, ordering=None, return_expr=False):
    #from pyeda.boolalg.bdd import bddvar, expr2bdd
    bdd = BDD()
    var_map = {}
    #print(f"TYPE: {type(tree)} MODULE: {type(tree).__module__}")
    inputs = sorted(tree.inputs()) if ordering is None else ordering
    print("Collected inputs:", tree.inputs)
    for var in inputs:
        bdd.declare(var)
    node = _build_bdd(tree, bdd, var_map)
    # Note logic_hash is the canonical hashed bdd representation
    expr = str(bdd.to_expr(node))
    logic_hash = hashlib.sha256(expr.encode('utf-8')).hexdigest()
    expr_str = to_symbolic_expr_str(tree)

    if return_expr:
        return logic_hash, expr_str
    else:
        return logic_hash

def explain_logic_hash(tree, ordering=None):
    bdd = BDD()
    var_map = {}
    inputs = sorted(tree.inputs()) if ordering is None else ordering
    for var in inputs:
        bdd.declare(var)
    node = _build_bdd(tree, bdd, var_map)
    expr_str = str(bdd.to_expr(node))
    hash_str = hashlib.sha256(expr_str.encode('utf-8')).hexdigest()
    _pretty_print_expr(expr_str)
    print("\nSHA256 Logic Hash:\n", hash_str)
    return expr_str, hash_str

def pretty_print(tree, indent=0):
    spacer = "  " * indent
    if isinstance(tree, LogicOp):
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
        lines.append(pretty_print(tree.codnition, indent + 1))
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
        logic_val = "TRUE" if tree.value == 1 else "FALSE"
        return f"{spacer}{logic_val}"
    elif isinstance(tree, LogicHole):
        return f"{spacer}HOLE({tree.name})"
    else:
        return f"{spacer}UNKNOWN({tree})"

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
        raise TypeError("Expected LogicNode got str")
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

# === BDD BACKEND ===
def to_bdd(tree: LogicNode, ordering=None) -> int:
    #bdd = _bdd.BDD()
    bdd = BDD()
    var_map = {}
    inputs = sorted(tree.operands) if ordering is None else ordering
    for var in inputs:
        bdd.declare(var)
    root = _build_bdd(tree, bdd, var_map)
    return bdd, root

def _build_bdd(tree: LogicNode, bdd: BDD, var_map: dict) -> int:
    if isinstance(tree, LogicConst):
        return bdd.true if tree.value else bdd.false

    elif isinstance(tree, LogicVar):
        #return bdd.var(tree.name)
        name = tree.name
        if name not in var_map:
            var_map[name] = bdd.var(name)
        return var_map[name]

    elif isinstance(tree, LogicHole):
        # Treat symbolic holes as unique BDD variables
        return bdd.var(tree.name)

    elif isinstance(tree, LogicOp):
        if tree.op == 'NOT':
            assert len(tree.children) == 1
            return ~_build_bdd(tree.children[0], bdd, var_map)
        elif tree.op == 'AND':
            return bdd.apply('and', *[_build_bdd(c, bdd, var_map) for c in tree.children])
        elif tree.op == 'OR':
            return bdd.apply('or', *[_build_bdd(c, bdd, var_map) for c in tree.children])
        elif tree.op == 'XOR':
            return bdd.apply('xor', *[_build_bdd(c, bdd, var_map) for c in tree.children])
        elif tree.op == 'XNOR':
            a, b = tree.children
            return ~bdd.apply('xor', _build_bdd(a, bdd, var_map), _build_bdd(b, bdd, var_map))
        elif tree.op == "MUX":
            # Mux(cond, a, b) = (cond & a) | (~cond & b)
            cond, a, b = (_build_bdd(c, bdd, var_map) for c in tree.children)
            return bdd.apply("or", 
                             bdd.apply("and", cond, a),
                             bdd.apply("and", bdd.apply("not", cond), b))
        elif tree.op == "IF":
            cond     = _build_bdd(tree.children[0], bdd, var_map)
            t_branch = _build_bdd(tree.children[1], bdd, var_map)
            e_branch = _build_bdd(tree.children[2], bdd, var_map)
            return (cond & t_branch) | (~cond & e_branch)
        elif tree.op == "EQ":
            a = _build_bdd(tree.children[0], bdd, var_map)
            b = _build_bdd(tree.children[1], bdd, var_map)
            return (a & b) | (~a & ~b)
            # Or: return ~(a ^ b)
        else:
            raise ValueError(f"Unknown logic operator: {tree.op}")

    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")

# === SYMPY BACKEND ===
from sympy.logic.boolalg import BooleanTrue, BooleanFalse
def to_sympy_expr(tree: LogicNode):
    if isinstance(tree, LogicConst):
        val = int(tree.value)
        #result = sympify(bool(val))
        #print(f"[SYM CONST] Interpreting LogicConst({tree.value}) as {val} ({type(val)})")
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

