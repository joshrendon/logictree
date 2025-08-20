from tests.utils import gate_count, literal_sig_set, flatten_or, flatten_and, leaves
from logictree.nodes.ops.gates import NotOp

def _rhs(sv, lower_sv_text_to_logic):
    return lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs

def test_if_true_false_becomes_identity(lower_sv_text_to_logic):
    sv = """
    module m(input logic a, output logic y);
      always_comb begin
        if (a) y = 1'b1; else y = 1'b0;
      end
    endmodule
    """
    rhs = _rhs(sv, lower_sv_text_to_logic)
    # Expect y == a structurally; either just Id(a) or (a & 1) | (~a & 0) simplified
    # Gate count should be 0 after simplification, but be tolerant of 1-level identity.
    cs = gate_count(rhs)
    assert cs["AND"] in (0, 1)
    assert cs["OR"] in (0, 1)
    # Ensure 'a' is positively required when output is 1
    # If you keep a simple Id, literal_sig_set returns {("a", True)}
    lits = literal_sig_set(rhs)
    assert ("a", True) in lits

def test_if_else_selects_values(lower_sv_text_to_logic):
    sv = """
    module m(input logic a,b,c, output logic y);
      always_comb begin
        if (a) y = b; else y = c;
      end
    endmodule
    """
    rhs = _rhs(sv, lower_sv_text_to_logic)
    # y == (a & b) | (~a & c)
    cs = gate_count(rhs)
    assert cs["OR"] == 1 and cs["AND"] == 2 and cs["NOT"] == 1

def test_if_elseif_else_three_way(lower_sv_text_to_logic):
    sv = """
    module m(input logic s0,s1, d0,d1,d2, output logic y);
      always_comb begin
        if (s0) y = d0;
        else if (s1) y = d1;
        else y = d2;
      end
    endmodule
    """
    rhs = _rhs(sv, lower_sv_text_to_logic)
    # y == (s0 & d0) | (~s0 & s1 & d1) | (~s0 & ~s1 & d2)
    # Counts: OR=2, AND= (1 + 2 + 2) = 5, NOT=2
    cs = gate_count(rhs)
    assert cs["OR"] == 2 and cs["NOT"] == 2 and cs["AND"] == 5

def test_if_w_eq_condition_reuses_equality(lower_sv_text_to_logic):
    sv = """
    module m(input logic [3:0] s, input logic d0, d1, output logic y);
      always_comb begin
        if (s == 4'b1001) y = d0; else y = d1;
      end
    endmodule
    """
    rhs = _rhs(sv, lower_sv_text_to_logic)
    # Structure should contain equality expansion AND-ed with d0 path and its negation with d1
    cs = gate_count(rhs)
    # Lower bound checks (exact numbers depend on your equality expansion shape)
    assert cs["OR"] >= 1 and cs["AND"] >= 1
