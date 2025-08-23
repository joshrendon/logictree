import pytest

pytestmark = [pytest.mark.unit]

from logictree.pipeline import lower_sv_text_to_logic
from tests.utils import flatten_and, gate_count, leaves


def _rhs(sv, lower_sv_text_to_logic):
    return lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs

def test_and_chain():
    sv = "module m(input logic a,b,c,d, output logic y); assign y = a & b & c & d; endmodule"
    rhs = _rhs(sv, lower_sv_text_to_logic)
    cs = gate_count(rhs)
    assert cs["AND"] == 3 and cs["OR"] == 0 and cs["XOR"] == 0
    # All four literals should appear once in the AND tree
    terms = set(leaves(flatten_and(rhs)))
    names = {getattr(t, "name", getattr(getattr(t, "var", t), "name", None)) for t in terms}
    assert names == {"a", "b", "c", "d"}

def test_or_of_products():
    sv = """
    module m(input logic a,b,c,d, output logic y);
      assign y = (a & b) | (c & d);
    endmodule
    """
    rhs = _rhs(sv, lower_sv_text_to_logic)
    cs = gate_count(rhs)
    assert cs["OR"] == 1 and cs["AND"] == 2

def test_xor_chain():
    sv = "module m(input logic a,b,c, output logic y); assign y = a ^ b ^ c; endmodule"
    rhs = _rhs(sv, lower_sv_text_to_logic)
    cs = gate_count(rhs)
    # Depending on lowering, XORs may be left-associated
    assert cs["XOR"] == 2 and cs["AND"] == 0 and cs["OR"] == 0

def test_not_precedence():
    sv = "module m(input logic a,b, output logic y); assign y = ~(a ^ b); endmodule"
    rhs = _rhs(sv, lower_sv_text_to_logic)
    cs = gate_count(rhs)
    assert cs["NOT"] == 1 and cs["XOR"] == 1

def test_mixed_precedence_and_parens():
    sv = "module m(input logic a,b,c, output logic y); assign y = a & (b | c); endmodule"
    rhs = _rhs(sv, lower_sv_text_to_logic)
    cs = gate_count(rhs)
    assert cs["AND"] == 1 and cs["OR"] == 1 and cs["XOR"] == 0
