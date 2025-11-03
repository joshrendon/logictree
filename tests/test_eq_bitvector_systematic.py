import pytest
import logging

pytestmark = [pytest.mark.unit]
from logictree.pipeline import lower_sv_text_to_logic
from tests.utils_bitselect import literal_sig_set, literal_bit_comparisons, gate_count
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.selects import Concat
from logictree.nodes.ops.ops import LogicVar
from logictree.transforms.to_primitives import to_primitives_logic_tree

log = logging.getLogger(__name__)

pytest.skip("Skipping bitvector systematic tests", allow_module_level=True)
@pytest.mark.parametrize("rng", sorted([(3,0), (0,3), (7,0), (0,7), (15,0)]))
@pytest.mark.parametrize("kvals_base", sorted([
    ("b", [0b0, 0b1, 0b1010, 0b0101]),
    ("h", [0x0, 0xF, 0xA, 0x5]),
    ("d", [0, 1, 3, 7, 15]),
]))
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

        log.info(f"Lowering Module:")
        log.info(f"{sv}")
        m = lower_sv_text_to_logic(sv)["m"]
        rhs = m.assignments["y"].rhs

        prims = to_primitives_logic_tree(rhs)

        # check exact literal terms (index, polarity)
        got = literal_bit_comparisons(prims, "s")
        expect = {(i, bool((k >> i) & 1)) for i in range(width)}
        assert got == expect

        # gate counts: NOT = zeros, AND = width-1
        log.debug(f"width: {width} bin(k).count(1): {bin(k).count('1')}")
        log.debug(f"k: {k}")
        zeros = width - bin(k).count("1")
        counts = gate_count(prims)
        assert counts["NOT"] == zeros
        assert counts["AND"] == max(width - 1, 0)
        # (No OR/XOR expected for equality expansion)
        assert counts["OR"] == 0
        assert counts["XOR"] == 0

def test_concat_ir_node():
    sv = "module m(input logic a,b,c,d, output logic y); assign y = ({a,b,c,d} == 4'b1001); endmodule"
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs
    # Ensure LHS is a Concat inside the Eq
    assert isinstance(rhs, EqOp)
    assert isinstance(rhs.lhs, Concat)
    assert [type(p) for p in rhs.lhs.parts] == [LogicVar, LogicVar, LogicVar, LogicVar]

def test_partselect_eq():
    sv = """
    module m(input logic [7:0] s, output logic y);
      assign y = (s[7:4] == 4'b1010);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs
    assert literal_sig_set(rhs, "s") == {'s[4]', 's[5]', 's[6]', 's[7]'}
    assert literal_bit_comparisons(rhs, "s") == {(7, True), (6, False), (5, True), (4, False)}


def test_concat_eq():
    sv = """
    module m(input logic a,b,c,d, output logic y);
      assign y = ({a,b,c,d} == 4'b1001);
    endmodule
    """
    rhs = lower_sv_text_to_logic(sv)["m"].assignments["y"].rhs
    # Using names instead of indices because signals are scalars
    log.info(f"type(rhs): {type(rhs).__name__}")
    log.info(f"rhs.children: {rhs.children}")
    log.info(f"circuit: {rhs}")
    log.info(f"literal_bit_comparisons(rhs): {literal_bit_comparisons(rhs)}")
    assert literal_bit_comparisons(rhs) == {("a", True), ("b", False), ("c", False), ("d", True)}

