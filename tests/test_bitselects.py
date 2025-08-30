import pytest

pytestmark = [pytest.mark.unit]

from logictree.nodes.ops import AndOp
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.ops import LogicConst
from logictree.nodes.selects import BitSelect
from logictree.pipeline import lower_sv_text_to_logic
from tests.utils_bitselect import assert_eq_const_terms


def test_bitselect_in_eq_const():
    """
    Verify that equality of a 2-bit vector against a constant literal
    is expanded into the expected per-bit equality checks.
    
    Example:
        assign y = (s == 2'b10);

    Should lower into:
        y = (s[0] == 1'd0) & (s[1] == 1'd1)
    """

    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    rhs = mod.assignments["y"].rhs

    
    # Top-level should be an AND of two EqOps
    assert isinstance(rhs, AndOp)

    # Collect both equality terms (order not guaranteed in AndOp)
    eqs = [rhs.left, rhs.right]
    for eq in eqs:
        assert isinstance(eq, EqOp)
        # LHS of each EqOp should be a BitSelect from the vector 's'
        lhs, rhs_const = eq.operands
        assert isinstance(lhs, BitSelect)
        assert lhs.base.name == "s"  # BitSelect should target signal 's'
        assert isinstance(rhs_const, LogicConst)  # RHS should be a logic constant

    # Extract (bit_index, const_value) pairs for easy semantic check
    terms = [(eq.operands[0].index, eq.operands[1].value) for eq in eqs]

    # Expect s[0] == 0 and s[1] == 1, regardless of order
    assert set(terms) == {(0, 0), (1, 1)}, f"Unexpected terms: {terms}"

def test_partselect_passthrough():
    sv = """
    module m(input logic [3:0] s, output logic [1:0] y);
      assign y = s[3:2];
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    from logictree.nodes.selects import PartSelect
    rhs = mod.assignments["y"].rhs
    assert isinstance(rhs, PartSelect)
    assert rhs.base.name == "s" and rhs.msb == 3 and rhs.lsb == 2

def test_concat_roundtrip():
    sv = """
    module m(input logic a,b,c,d, output logic [3:0] y);
      assign y = {a,b,c,d};
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    from logictree.nodes.selects import Concat
    rhs = mod.assignments["y"].rhs
    assert isinstance(rhs, Concat)
    assert [p.name for p in rhs.parts] == ["a","b","c","d"]

def test_eq_descending_range():
    sv = """
    module m(input logic [3:0] s, output logic y);
      assign y = (s == 4'b1001);
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    rhs = mod.assignments["y"].rhs

    # Expect semantic expansion to 1001 on 4 bits
    assert_eq_const_terms(rhs, 0b1001, 4, "s")

def test_eq_ascending_range():
    sv = """
    module m(input logic [0:3] s, output logic y);
      assign y = (s == 4'b1001);
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    rhs = mod.assignments["y"].rhs

    # Same semantic check, despite [0:3] syntax
    assert_eq_const_terms(rhs, 0b1001, 4, "s")
