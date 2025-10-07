import pytest
from sympy import Piecewise, true, simplify as sympy_simplify
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.ops import LogicVar, LogicConst, LogicOp
from logictree.nodes.ops.gates import OrOp, AndOp, NotOp
from logictree.transforms.simplify import simplify
from logictree.transforms.to_primitives import to_primitives_logic_tree
from logictree.analysis.depth import depth
from logictree.analysis.delay import delay
from logictree.transforms.to_sympy import to_sympy_expr
from logictree.nodes.ops.ite import ITEOp
import logging

log = logging.getLogger(__name__)

def test_iteop_end_to_end():
    a = LogicVar("a")
    b = LogicVar("b")
    node = ITEOp(b, LogicConst(2), ITEOp(a, LogicConst(1), LogicConst(0)))
    log.info(f"Circuit: {node}")

    # depth
    d = depth(node)
    assert isinstance(d, int)
    assert d > 0
    log.info(f"Circuit depth: {d}")

    # delay
    dl = delay(node)
    assert dl >= d
    log.info(f"Circuit delay: {dl}")

    # simplify
    simp = simplify(node)
    assert isinstance(simp, ITEOp)
    log.info(f"Circuit simplified: {simp}")

    # primitives
    prim = to_primitives_logic_tree(node)
    assert isinstance(prim, OrOp)
    assert any(isinstance(c, AndOp) for c in prim.operands)
    log.info(f"Circuit prim: {prim}")

    #prim_str = str(prim)
    #assert "AndOp" in prim_str or "OrOp" in prim_str

    # sympy
    expr = to_sympy_expr(node)
    log.info(f"Circuit to_sympy_expr: {expr}")
    expected = Piecewise(
        (2, to_sympy_expr(b)),
        (1, to_sympy_expr(a)),
        (0, true),
    )
    log.info(f"Expected circuit: {expected}")
    assert sympy_simplify(expr - expected) == 0
