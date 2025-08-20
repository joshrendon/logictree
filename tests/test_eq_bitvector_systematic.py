import pytest
from tests.utils import literal_sig_set, gate_count
from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic

@pytest.mark.parametrize("rng", [(3,0), (0,3), (7,0), (0,7), (15,0)])
@pytest.mark.parametrize("kvals_base", [
    ("b", [0b0, 0b1, 0b1010, 0b0101]),
    ("h", [0x0, 0xF, 0xA, 0x5]),
    ("d", [0, 1, 3, 7, 15]),
])
def test_eq_bitvector_systematic(rng, kvals_base):
    hi, lo = rng
    width = abs(hi - lo) + 1
    base, kvals = kvals_base

    # keep values in range
    kvals = [k & ((1 << width) - 1) for k in kvals]

    for k in kvals:
        literal = f"{width}'{base}{k:x}" if base == "h" else f"{width}'{base}{k:b}" if base == "b" else f"{width}'{base}{k}"
        sv = f"""
        module m(input logic [{hi}:{lo}] s, output logic y);
          assign y = (s == {literal});
        endmodule
        """

        rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs

        # check exact literal terms (index, polarity)
        got = literal_sig_set(rhs, only_name="s")
        expect = {(i, bool((k >> i) & 1)) for i in range(width)}
        assert got == expect

        # gate counts: NOT = zeros, AND = width-1
        zeros = width - bin(k).count("1")
        counts = gate_count(rhs)
        assert counts["NOT"] == zeros
        assert counts["AND"] == max(width - 1, 0)
        # (No OR/XOR expected for equality expansion)
        assert counts["OR"] == 0
        assert counts["XOR"] == 0


def test_partselect_eq(lower_sv_text_to_logic):
    sv = """
    module m(input logic [7:0] s, output logic y);
      assign y = (s[7:4] == 4'b1010);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs
    assert literal_sig_set(rhs, only_name="s") == {(7, True), (6, False), (5, True), (4, False)}


def test_concat_eq(lower_sv_text_to_logic):
    sv = """
    module m(input logic a,b,c,d, output logic y);
      assign y = ({a,b,c,d} == 4'b1001);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs
    # Using names instead of indices because signals are scalars
    assert literal_sig_set(rhs) == {("a", True), ("b", False), ("c", False), ("d", True)}
