from logictree.nodes import ops, control, base, hole
import itertools
import re
from dd.autoref import BDD
from typing import Dict, Tuple, Union, Optional

def _build_bdd(tree: base.LogicTreeNode, bdd: BDD, var_map: dict) -> int:
    if isinstance(tree, ops.LogicConst):
        return bdd.true if tree.value else bdd.false

    elif isinstance(tree, ops.LogicVar):
        #return bdd.var(tree.name)
        name = tree.name
        if name not in var_map:
            var_map[name] = bdd.var(name)
        return var_map[name]

    elif isinstance(tree, hole.LogicHole):
        # Treat symbolic holes as unique BDD variables
        return bdd.var(tree.name)

    elif isinstance(tree, ops.LogicOp):
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
