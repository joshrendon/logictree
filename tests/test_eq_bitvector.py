import pytest

pytestmark = [pytest.mark.unit]

from logictree.pipeline import lower_sv_text_to_logic
from tests.utils import gate_count, literal_sig_set


def test_eq_bitvector_const():
    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs

    # Expect s[1] = 1, s[0] = 0
    assert literal_sig_set(rhs, only_name="s") == {(1, True), (0, False)}

    counts = gate_count(rhs)
    assert counts["AND"] == 1
    assert counts["NOT"] == 1
    assert counts["OR"] == 0 and counts["XOR"] == 0
