import logging

import pytest
from sympy import Not, symbols
from sympy import simplify as sympy_simplify

from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.transforms.to_primitives import to_primitives_logic_tree
from logictree.transforms.to_sympy import to_sympy_expr

log = logging.getLogger(__name__)


@pytest.mark.unit
def test_iteop_multibit_true_branch_expands():
    # y = if(b) 2(2’b10) else 0
    b = LogicVar("b")
    node = ITEOp(b, LogicConst(2, width=2), LogicConst(0, width=2))

    prim = to_primitives_logic_tree(node)
    log.info(f"Primitives: {prim}")

    # Should return a Concat of two bits
    assert prim.__class__.__name__ == "Concat"
    assert len(prim.parts) == 2

    # Convert each bit to sympy
    sym_bits = [to_sympy_expr(bit) for bit in prim.parts]

    # Expected behavior:
    # bit0 = 0 (since 2 = 10₂)
    # bit1 = b
    b_sym = symbols("b")
    expected_bits = [0, b_sym]

    for got, exp in zip(sym_bits, expected_bits):
        assert sympy_simplify(got - exp) == 0


@pytest.mark.unit
def test_iteop_multibit_false_branch_expands():
    # y = if(b) 0 else 3(2’b11)
    b = LogicVar("b")
    node = ITEOp(b, LogicConst(0, width=2), LogicConst(3, width=2))

    prim = to_primitives_logic_tree(node)
    log.info(f"Primitives: {prim}")

    assert prim.__class__.__name__ == "Concat"
    assert len(prim.parts) == 2

    sym_bits = [to_sympy_expr(bit) for bit in prim.parts]

    b_sym = symbols("b")
    # When b=1 => 0, when b=0 => constant 3 => both bits 1
    expected_bits = [Not(b_sym), Not(b_sym)]

    for got, exp in zip(sym_bits, expected_bits):
        assert sympy_simplify(got - exp) == 0


@pytest.mark.unit
def test_iteop_multibit_both_branches():
    # y = if(b) 2(10₂) else 1(01₂)
    b = LogicVar("b")
    node = ITEOp(b, LogicConst(2, width=2), LogicConst(1, width=2))

    prim = to_primitives_logic_tree(node)
    log.info(f"Primitives: {prim}")

    assert prim.__class__.__name__ == "Concat"
    assert len(prim.parts) == 2

    sym_bits = [to_sympy_expr(bit) for bit in prim.parts]

    b_sym = symbols("b")
    # bit0 = mux(b, 0, 1) = ~b
    # bit1 = mux(b, 1, 0) = b
    expected_bits = [Not(b_sym), b_sym]

    for got, exp in zip(sym_bits, expected_bits):
        assert sympy_simplify(got - exp) == 0
