import logging
from pathlib import Path

import pytest
from sympy import Piecewise
from sympy import simplify as sympy_simplify

from logictree.analysis.delay import delay
from logictree.analysis.depth import depth
from logictree.nodes.ops.gates import AndOp, OrOp
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.transforms.simplify import simplify
from logictree.transforms.to_primitives import to_primitives_logic_tree
from logictree.transforms.to_sympy import to_sympy_expr
from logictree.utils.display import pretty_inline, pretty_print
from logictree.utils.output import render_png_multi
from logictree.utils.schematic import render_schematic
from tests.utils.viz_helpers import assert_viz

log = logging.getLogger(__name__)


@pytest.mark.unit
def test_nested_two_conditions():
    # y = if(b) 2 else if(a) 1 else 0
    a, b = LogicVar("a"), LogicVar("b")
    node = ITEOp(b, LogicConst(2), ITEOp(a, LogicConst(1), LogicConst(0)))
    log.info(f"Circuit: {node}")

    # depth & delay
    assert depth(node) == 2
    assert delay(node) == 2
    log.info(f"Circuit depth: {depth(node)}, delay: {delay(node)}")

    # simplify collapses nested ITE
    simp = simplify(node)
    assert isinstance(simp, ITEOp)
    assert "ITE" in str(simp)
    log.info(f"Circuit simplified: {simp}")

    # primitives are expressed in AND/OR form
    prim = to_primitives_logic_tree(node)
    log.info(f"Circuit prim: {prim}")
    #assert isinstance(prim, OrOp)
    #assert any(isinstance(c, AndOp) for c in prim.operands)
    #assert any(isinstance(c, AndOp) for c in prim)
    assert any(
        isinstance(sub, AndOp)
        for expr in prim
        for sub in getattr(expr, "operands", [])
    )

    # sympy equivalence
    expr = to_sympy_expr(node)
    log.info(f"Circuit to_sympy_expr(node): {expr}")
    expected = Piecewise(
        (2, to_sympy_expr(b)), 
        (1, to_sympy_expr(a)), 
        (0, True)
    )
    log.info(f"Circuit expected sympy expr: {expected}")
    assert sympy_simplify(expr - expected) == 0
    png = assert_viz(node, "ite_nested_two_conditions")
    log.info(f"Visualization written to {png}")


@pytest.mark.unit
def test_three_way_priority_chain():
    # y = if(c) 3 else if(b) 2 else if(a) 1 else 0
    a, b, c = LogicVar("a"), LogicVar("b"), LogicVar("c")
    node = ITEOp(c, LogicConst(3),
                 ITEOp(b, LogicConst(2),
                       ITEOp(a, LogicConst(1), LogicConst(0))))

    log.info(f"Circuit: {node}")
    log.info(f"{pretty_print(node)}")
    # depth & delay
    assert depth(node) == 3
    assert delay(node) == 3
    log.info(f"Circuit depth: {depth(node)}, delay: {delay(node)}")

    # simplify keeps multi-branch priority structure
    simp = simplify(node)
    assert isinstance(simp, ITEOp)
    log.info(f"Circuit simplified: {simp}")

    # primitives: cascade of AND/OR expansions
    prim = to_primitives_logic_tree(node)
    #prim_list = prim if isinstance(prim, list) else [prim]
    #assert "&" in prim_str and "|" in prim_str
    if isinstance(prim, list):
        for bit_expr in prim:
            prim_str = str(bit_expr)
            assert isinstance(bit_expr, OrOp)
            assert "&" in prim_str and "|" in prim_str
    else:
        assert isinstance(bit_expr, OrOp)
        prim_str = str(prim)
        assert "&" in prim_str and "|" in prim_str
    log.info(f"Circuit str(prim): {prim}")
    log.info(f"Circuit prim: {pretty_print(prim)}")
    log.info(f"Circuit prim: {pretty_inline(prim)}")
    log.info(f"Circuit repr(prim): {repr(prim)}")

    #png = render_png_multi(prim, name="ite_priority_chain_multi_prim", edge_style="polyline")
    png = render_png_multi(prim, name="ite_priority_chain_multi_prim")
    assert Path(png).exists()
    png = assert_viz(prim, "ite_nested_three_way_priority_chain_to_prim")
    log.info(f"Visualization written to {png}")

    # sympy equivalence
    expr = to_sympy_expr(node)
    log.info(f"Circuit to_sympy_expr(node): {expr}")
    expected = Piecewise(
        (3, to_sympy_expr(c)), 
        (2, to_sympy_expr(b)), 
        (1, to_sympy_expr(a)), 
        (0, True)
    )
    log.info(f"Circuit expected sympy expr: {expected}")
    assert sympy_simplify(expr - expected) == 0
    png = assert_viz(node, "ite_nested_three_way_priority_chain")
    log.info(f"Visualization written to {png}")
    render_schematic(node, "output/ite_three_way_schematic.png")


@pytest.mark.unit
def test_redundant_condition_simplification():
    # y = if(a) 1 else if(a) 2 else 0  -> should simplify to ITE(a, 1, 0)
    a = LogicVar("a")
    node = ITEOp(a, LogicConst(1), ITEOp(a, LogicConst(2), LogicConst(0)))
    log.info(f"Circuit: {node}")

    simp = simplify(node)
    log.info(f"Circuit simplified: {simp}")
    assert isinstance(simp, ITEOp)
    simp_str = str(simp)
    # Redundant nested 'a' should collapse away
    assert "2" not in simp_str

    # Sympy equivalence
    expr = to_sympy_expr(node)
    log.info(f"Circuit to_sympy_expr(node): {expr}")
    expected = Piecewise(
        (1, to_sympy_expr(a)),
        (0, True)
    )
    log.info(f"Circuit expected sympy expr: {expected}")
    assert sympy_simplify(expr - expected) == 0
    png = assert_viz(node, "ite_redundant_cond_simp")
    log.info(f"Visualization written to {png}")
