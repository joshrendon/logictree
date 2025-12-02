# tests/sympy_case_equiv_demo.py
import logging

import sympy as sp
from sympy import And, Eq, Not, Or, Xor, simplify_logic, symbols

log = logging.getLogger(__name__)

def test_sympy_case_valid():
    from sympy import And, Not, Or, simplify_logic
    a,b,sel = symbols("a b sel", boolean=True)
    
    expr_case = Or(And(Not(sel), a), And(sel, b))
    expr_mux = Or(And(sel, b), And(Not(sel), a))
    xor_diff = Xor(expr_case, expr_mux)
    simplified = simplify_logic(xor_diff, form='dnf')
    log.info(f"Case expr: {expr_case}")
    log.info(f"Mux expr: {expr_mux}")
    log.info(f"XOR diff: {xor_diff}")
    log.info(f"XOR diff {simplified}")  # prints False
    assert simplified is sp.false or not simplified
    log.info("CaseStatement and LogicMux are logically equivalent!")

def test_sympy_case_equiv_eq_bad():
    # Create Boolean symbols
    sel, a, b = sp.symbols("sel a b", boolean=True)
    
    # --- CASE STATEMENT FORM ---
    # equivalent to:
    # case(sel)
    #   0: out = a;
    #   1: out = b;
    # endcase
    ##case_expr = Or(
    ##    And(Not(sel), a),  # sel==0 → a
    ##    And(sel, b)           # sel==1 → b
    ##)
    # Intentional bad use of Eq() functions
    case_expr_bad = Or(
        And(Eq(sel, False), a),  # sel==0 → a
        And(Eq(sel, True), b)           # sel==1 → b
    )
    
    # --- MUX FORM ---
    # equivalent to mux(sel, b, a)
    # (sel ? b : a)
    mux_expr = Or(
        And(sel, b),
        And(Not(sel), a)
    )
    
    # --- Comparison ---
    xor_diff = Xor(case_expr_bad, mux_expr)
    simplified = simplify_logic(xor_diff, form='dnf')
    
    log.info(f"CASE expr: {case_expr_bad}")
    log.info(f"MUX  expr: {mux_expr}")
    log.info(f"XOR diff: {xor_diff}")
    log.info(f"Simplified diff: {simplified}")
    
    assert simplified is sp.true or simplified
    log.info("\nCaseStatement and LogicMux are NOT logically equivalent!")
