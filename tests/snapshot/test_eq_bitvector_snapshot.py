import logging

from logictree.api import lower_sv_text_to_logic
from logictree.transforms.to_primitives import to_primitives_logic_tree
from logictree.utils.display import pretty_print
from tests.utils_bitselect import gate_count, literal_bit_comparisons, literal_sig_set

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def test_eq_bitvector_snapshot():
    sv_code = """
    module m(input logic [1:0] s, output logic y);
        assign y = (s == 2'b10);
    endmodule
    """

    modules = lower_sv_text_to_logic(sv_code)
    m = modules["m"]
    assign = m.assignments["y"]
    original = assign.rhs

    # === 1. Original (symbolic) view ===
    logger.debug("ORIGINAL TREE:")
    print("\n--- ORIGINAL ---")
    print(pretty_print(original))

    # === 2. Extract literal signals and comparisons ===
    sigs = literal_sig_set(original, "s")
    comps = literal_bit_comparisons(original, "s")

    logger.debug(f"Literals: {sigs}")
    logger.debug(f"literal_bit_comparisons: {comps}")

    assert sigs == {"s[0]", "s[1]"}
    assert comps == {(0, False), (1, True)}

    # === 3. Count gates (symbolic form) ===
    symbolic_counts = gate_count(original)
    print("\nSymbolic gate count:", symbolic_counts)
    assert symbolic_counts["AND"] == 1
    assert symbolic_counts["EQ"] == 2

    # === 4. Lower to canonical (primitive) gates ===
    lowered = to_primitives_logic_tree(original)
    print("\n--- LOWERED ---")
    print(pretty_print(lowered))

    # === 5. Count gates (canonical form) ===
    canonical_counts = gate_count(lowered)
    print("\nCanonical gate count:", canonical_counts)
    assert canonical_counts["AND"] == 1
    assert canonical_counts["NOT"] == 1

    # === 6. Optional: Dump JSON for visual inspection ===
    # from logictree.utils.serialize import logic_tree_to_json
    # with open("snapshot_eq_bitvector.json", "w") as f:
    #     json.dump(logic_tree_to_json(original), f, indent=2)

