from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from logictree.nodes.ops import LogicVar, AndOp, NotOp, OrOp
from logictree.nodes.control.assign import LogicAssign
from tests.utils import assert_eq_1001_terms

def test_bitselect_in_eq_const():
    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    rhs = mod.assignments["y"].rhs
    from logictree.nodes.selects import BitSelect
    assert isinstance(rhs, AndOp)
    assert isinstance(rhs.left, BitSelect)
    assert rhs.left.base.name == "s" and rhs.left.index == 1
    assert isinstance(rhs.right, NotOp)
    assert isinstance(rhs.right.operand, BitSelect)
    assert rhs.right.operand.base.name == "s" and rhs.right.operand.index == 0

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
    assert_eq_1001_terms(rhs, "s")
    # Expect (s[3] & ~s[2] & ~s[1] & s[0]) with left=MSB
    from logictree.nodes.selects import BitSelect
    from logictree.nodes.ops.gates import AndOp, NotOp
    assert isinstance(rhs, AndOp)
    #assert isinstance(rhs.left, BitSelect) and rhs.left.index == 3

def test_eq_ascending_range():
    sv = """
    module m(input logic [0:3] s, output logic y);
      assign y = (s == 4'b1001);
    endmodule
    """
    mod = lower_sv_text_to_logic(sv)["m"]
    rhs = mod.assignments["y"].rhs
    assert_eq_1001_terms(rhs, "s")
    # Expect indices [0..3] still map LSB->index 0, MSB->index 3
    #assert isinstance(rhs.left, BitSelect) and rhs.left.index == 3
