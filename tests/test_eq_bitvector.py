import pytest

pytestmark = [pytest.mark.integration]

from logictree.pipeline import lower_sv_text_to_logic
from logictree.utils.display import pretty_print
from tests.utils_bitselect import gate_count, literal_sig_set, literal_bit_comparisons
from logictree.transforms.to_primitives import to_primitives_logic_tree

import logging

log = logging.getLogger(__name__)

def test_eq_bitvector_const():
    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs

    # Expect s[1] = 1, s[0] = 0
    log.debug(f"Literals: {literal_sig_set(rhs, 's')}")
    log.debug(f"literal_bit_comparisons: {literal_bit_comparisons(rhs, 's')}")
    assert literal_bit_comparisons(rhs, "s") == {(0, False),(1, True)}

    # measure the gate counts for the semantic level circuit (pre-lowering)
    counts = gate_count(rhs)
    assert counts["AND"] == 1
    assert counts["EQ"] == 2
    assert counts["OR"] == 0


    # measure the gate counts for the primitive circuit (lowered circuit)
    lowered = to_primitives_logic_tree(rhs)
    primitive_counts = gate_count(lowered)
    log.info(f"Gate count (after lowering): circuit:\n{repr(lowered)}\ncounts: {primitive_counts}")
    assert primitive_counts["AND"] == 1
    assert primitive_counts["NOT"] == 1
    assert primitive_counts["EQ"] == 0
