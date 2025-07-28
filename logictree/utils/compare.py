from logictree.nodes import ops, control, base, hole
#from logictree.nodes import LogicOp, LogicVar, LogicConst, LogicHole, LogicNode, CaseStatement, CaseItem, IfStatement, LogicAssign
#import hashlib
import itertools
import re
from dd.autoref import BDD
from typing import Dict, Tuple, Union, Optional
from logictree.utils.build import _build_bdd

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

# === BDD BACKEND ===
def to_bdd(tree: base.LogicTreeNode, ordering=None) -> int:
    #bdd = _bdd.BDD()
    bdd = BDD()
    var_map = {}
    inputs = sorted(tree.operands) if ordering is None else ordering
    for var in inputs:
        bdd.declare(var)
    root = _build_bdd(tree, bdd, var_map)
    return bdd, root

