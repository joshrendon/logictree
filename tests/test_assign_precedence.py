import pytest
pytestmark = [pytest.mark.unit]
from logictree.pipeline import lower_sv_text_to_logic
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp, XorOp

@pytest.mark.parametrize("rhs, expect_top", [
    ("a & b | c", OrOp),      # & before |
    ("a | b & c", OrOp),      # & binds tighter
    ("a ^ b & c", XorOp),     # & before ^
    ("~a & b", AndOp),        # unary ~ binds tight
    ("(a & b) | c", OrOp),    # parentheses force shape
])
def test_precedence(rhs, expect_top):
    sv = f"module m(input logic a,b,c, output logic y); assign y = {rhs}; endmodule"
    mod = lower_sv_text_to_logic(sv)["m"]
    assert isinstance(mod.assignments["y"].rhs, expect_top)
