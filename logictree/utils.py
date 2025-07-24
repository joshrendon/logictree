# logictree/utils.py

from logictree.nodes import LogicOp, LogicVar, LogicConst, LogicHole
import hashlib
import itertools
import re
from dd import autoref as _bdd
from sympy import symbols
from sympy.logic.boolalg import And, Or, Not
from rich.console import Console
from rich.text import Text
import graphviz

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
    bdd = _bdd.BDD()
    #print(f"TYPE: {type(tree)} MODULE: {type(tree).__module__}")
    inputs = sorted(tree.inputs()) if ordering is None else ordering
    print("Collected inputs:", tree.inputs)
    for var in inputs:
        bdd.declare(var)
    node = _build_bdd(tree, bdd)
    # Note logic_hash is the canonical hashed bdd representation
    expr = str(bdd.to_expr(node))
    logic_hash = hashlib.sha256(expr.encode('utf-8')).hexdigest()
    expr_str = to_symbolic_expr_str(tree)

    if return_expr:
        return logic_hash, expr_str
    else:
        return logic_hash

def explain_logic_hash(tree, ordering=None):
    bdd = _bdd.BDD()
    inputs = sorted(tree.operands) if ordering is None else ordering
    for var in inputs:
        bdd.declare(var)
    node = _build_bdd(tree, bdd)
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
    elif isinstance(tree, LogicVar):
        return f"{spacer}VAR({tree.name})"
    elif isinstance(tree, LogicConst):
        return f"{spacer}CONST({tree.value})"
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
def to_bdd(tree, ordering=None):
    bdd = _bdd.BDD()
    inputs = sorted(tree.operands) if ordering is None else ordering
    for var in inputs:
        bdd.declare(var)
    return _build_bdd(tree, bdd)

def _build_bdd(tree, bdd):
    if isinstance(tree, LogicConst):
        return bdd.true if tree.value else bdd.false

    elif isinstance(tree, LogicVar):
        return bdd.var(tree.name)

    elif isinstance(tree, LogicHole):
        # Treat symbolic holes as unique BDD variables
        return bdd.var(tree.name)

    elif isinstance(tree, LogicOp):
        if tree.op == 'NOT':
            assert len(tree.children) == 1
            return ~_build_bdd(tree.children[0], bdd)
        elif tree.op == 'AND':
            return bdd.apply('and', *[_build_bdd(c, bdd) for c in tree.children])
        elif tree.op == 'OR':
            return bdd.apply('or', *[_build_bdd(c, bdd) for c in tree.children])
        elif tree.op == 'XOR':
            return bdd.apply('xor', *[_build_bdd(c, bdd) for c in tree.children])
        elif tree.op == 'XNOR':
            a, b = tree.children
            return ~bdd.apply('xor', _build_bdd(a, bdd), _build_bdd(b, bdd))
        elif tree.op == "MUX":
            # Mux(cond, a, b) = (cond & a) | (~cond & b)
            cond, a, b = (_build_bdd(c, bdd) for c in tree.children)
            return bdd.apply("or", 
                             bdd.apply("and", cond, a),
                             bdd.apply("and", bdd.apply("not", cond), b))
        else:
            raise ValueError(f"Unknown logic operator: {tree.op}")

    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")

# === SYMPY BACKEND ===
def to_sympy_expr(tree):
    if tree.op is None:
        return symbols(tree.name)
    children = [to_sympy_expr(c) for c in tree.children]
    if tree.op == 'AND':
        return And(*children)
    elif tree.op == 'OR':
        return Or(*children)
    elif tree.op == 'NOT':
        return Not(children[0])
    elif tree.op == 'NAND':
        return Not(And(*children))
    elif tree.op == 'NOR':
        return Not(Or(*children))
    elif tree.op == 'XOR':
        a, b = children
        return Or(And(a, Not(b)), And(Not(a), b))
    elif tree.op == 'XNOR':
        a, b = children
        return Or(And(a, b), And(Not(a), Not(b)))
    else:
        raise NotImplementedError(f"Unsupported operator: {tree.op}")

