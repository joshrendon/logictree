from __future__ import annotations

import logging

from dd.autoref import BDD, Function

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect

log = logging.getLogger(__name__)

def build_bdd(tree, bdd, var_map):

    if isinstance(tree, LogicConst):
        return bdd.true if tree.value else bdd.false

    elif isinstance(tree, LogicVar):
        if tree.name not in var_map:
            var_map[tree.name] = bdd.var(tree.name)
        return var_map[tree.name]

    elif isinstance(tree, NotOp):
        return bdd.apply('not', build_bdd(tree.operand, bdd, var_map))

    elif isinstance(tree, AndOp):
        return bdd.apply('and', *[build_bdd(c, bdd, var_map) for c in tree.children])

    elif isinstance(tree, OrOp):
        return bdd.apply('or', *[build_bdd(c, bdd, var_map) for c in tree.children])

    elif isinstance(tree, EqOp):
        lhs = build_bdd(tree.operands[0], bdd, var_map)
        rhs = build_bdd(tree.operands[1], bdd, var_map)
        return _eq_bdd(lhs, rhs, bdd)

    elif isinstance(tree, NeqOp):
        lhs = build_bdd(tree.operands[0], bdd, var_map)
        rhs = build_bdd(tree.operands[1], bdd, var_map)
        return _neq_bdd(lhs, rhs, bdd)

    elif isinstance(tree, LogicMux):
        sel = build_bdd(tree.selector, bdd, var_map)
        t = build_bdd(tree.if_true, bdd, var_map)
        f = build_bdd(tree.if_false, bdd, var_map)

        assert hasattr(sel, 'bdd'), f"sel is not a BDD node: {sel}"
        assert hasattr(t, 'bdd'), f"if_true is not a BDD node: {t}"
        assert hasattr(f, 'bdd'), f"if_false is not a BDD node: {f}"
        return bdd.ite(sel, t, f)

    elif isinstance(tree, LogicAssign):
        log.debug("LogicAssign")

    elif isinstance(tree, BitSelect):
        log.debug("BitSelect")
        assert isinstance(tree.base, LogicVar), "Only LogicVar base supported for BitSelect"
        assert isinstance(tree.index, LogicConst), "BitSelect index must be constant"
        base_var = tree.base.name
    
        # If the signal is scalar, just use the base_var directly
        if base_var not in var_map:
            var_map[base_var] = bdd.var(base_var)
        return var_map[base_var]

    ##elif isinstance(tree, BitSelect):
    ##    log.debug("BitSelect")
    ##    base = build_bdd(tree.base, bdd, var_map)
    ##    idx = tree.index
    ##    if isinstance(idx, LogicConst):
    ##        # BDD variable name for sel[0] → maybe encode as "sel[0]"
    ##        base_var = f"{tree.base.name}[{idx.value}]"
    ##        if base_var not in var_map:
    ##            var_map[base_var] = bdd.var(base_var)
    ##        return var_map[base_var]
    ##    else:
    ##        raise TypeError(f"Dynamic bit-select not supported in BDDs: {tree}")
    elif isinstance(tree, PartSelect):
        log.debug("PartSelect")
    elif isinstance(tree, Concat):
        log.debug("Concat")

    raise TypeError(f"Unsupported node: {tree}")



def _eq_bdd(lhs, rhs, bdd: BDD) -> Function:
    log.debug(f"_eq_bdd types: lhs={type(lhs)}, rhs={type(rhs)}")
    if isinstance(lhs, tuple) and isinstance(rhs, tuple):
        if len(lhs) != len(rhs):
            raise ValueError("Mismatched vector lengths in EqOp")
        bits = [bdd.apply("xnor", l, r) for l, r in zip(lhs, rhs)]
        return _reduce_and(bits, bdd)
    elif isinstance(lhs, Function) and isinstance(rhs, Function):
        return ~bdd.apply("xor", lhs, rhs)
    raise TypeError("Unsupported EqOp operand types")


def _neq_bdd(lhs, rhs, bdd: BDD) -> Function:
    if isinstance(lhs, tuple) and isinstance(rhs, tuple):
        if len(lhs) != len(rhs):
            raise ValueError("Mismatched vector lengths in NeqOp")
        bits = [bdd.apply("xor", l, r) for l, r in zip(lhs, rhs)]
        return _reduce_or(bits, bdd)
    elif isinstance(lhs, Function) and isinstance(rhs, Function):
        return bdd.apply("xor", lhs, rhs)
    raise TypeError("Unsupported NeqOp operand types")


def _reduce_and(bits: list[Function], bdd: BDD) -> Function:
    result = bits[0]
    for bit in bits[1:]:
        result = bdd.apply("and", result, bit)
    return result


def _reduce_or(bits: list[Function], bdd: BDD) -> Function:
    result = bits[0]
    for bit in bits[1:]:
        result = bdd.apply("or", result, bit)
    return result

