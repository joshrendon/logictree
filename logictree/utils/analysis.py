from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicOp
from logictree.nodes.types import GATE_TYPES
import hashlib
from dd.autoref import BDD
#from rich.console import Console
#from rich.text import Text
from typing import Dict, Tuple, Union, Optional
from logictree.utils.build import _build_bdd
from logictree.utils.display import to_symbolic_expr_str, _pretty_print_expr

def count_gate_type(tree, gate_name):
    if isinstance(tree, LogicOp):
        return int(tree.name == gate_name) + sum(count_gate_type(inp, gate_name) for inp in tree.inputs())
    elif isinstance(tree, LogicTreeNode):
        return 0
    return 0

def gate_count(tree):
    return {g: count_gate_type(tree, g) for g in GATE_TYPES}

def gate_summary(tree):
    counts = gate_count(tree)
    return ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)

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
