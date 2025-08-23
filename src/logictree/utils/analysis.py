import hashlib
import logging
from typing import Dict

from dd.autoref import BDD

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicOp
from logictree.nodes.types import GATE_TYPES
from logictree.utils.build import _build_bdd
from logictree.utils.display import _pretty_print_expr, to_symbolic_expr_str

log = logging.getLogger(__name__)

def count_gate_type(tree, gate_name):
    if isinstance(tree, LogicOp):
        return int(tree.name == gate_name) + sum(count_gate_type(inp, gate_name) for inp in tree.inputs())
    elif isinstance(tree, LogicTreeNode):
        return 0
    return 0

# NEW: return the full breakdown as a dict
def gate_breakdown(tree) -> Dict[str, int]:
    return {g: count_gate_type(tree, g) for g in GATE_TYPES}

# CHANGED: return a scalar total (tests expect an int)
def gate_count(tree) -> int:
    counts = gate_breakdown(tree)
    return sum(counts.values())

def gate_summary(tree):
    counts = gate_breakdown(tree)
    return ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)

def _as_var_name(v) -> str:
    # Make sure BDD gets string variable names
    return getattr(v, "name", str(v))

def get_logic_hash(tree, ordering=None, return_expr=False):
    bdd = BDD()
    var_map = {}

    # Collect inputs (prefer an explicit API if your nodes provide it)
    inputs = tree.inputs() if hasattr(tree, "inputs") else (tree.children if hasattr(tree, "children") else [])
    log.info("Collected inputs: %s", inputs)

    # Declare BDD vars as strings
    for var in inputs:
        bdd.declare(_as_var_name(var))

    node = _build_bdd(tree, bdd, var_map)
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

    inputs = (tree.inputs() if hasattr(tree, "inputs") else [])
    if ordering is not None:
        inputs = ordering
    else:
        # Best‐effort stable order by var name
        inputs = sorted(inputs, key=_as_var_name)

    for var in inputs:
        bdd.declare(_as_var_name(var))

    node = _build_bdd(tree, bdd, var_map)
    expr_str = str(bdd.to_expr(node))
    hash_str = hashlib.sha256(expr_str.encode('utf-8')).hexdigest()
    _pretty_print_expr(expr_str)
    log.info("\nSHA256 Logic Hash:\n:%s", hash_str)
    return expr_str, hash_str
