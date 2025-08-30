# tests/test_sv_to_logic_tree_fields.py
import dataclasses

from logictree.nodes import AndOp, BitSelect, LogicVar, NotOp
from logictree.pipeline import lower_sv_text_to_logic
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from logictree.utils.debug import assert_no_fields


def check_for_bad_fields(obj):
    bad_fields = []
    for name, val in vars(obj).items():
        if isinstance(val, dataclasses.Field):
            bad_fields.append((name, val))
    return bad_fields

def test_all_lowered_nodes_have_no_fields():
    sv = """
    module m(input logic a, b, output logic y);
      assign y = a & b;
    endmodule
    """
    module_map = lower_sv_text_to_logic(sv)
    for name, tree in module_map.items():
        assert_no_fields(tree, name=name)

def test_lowerer_current_module_has_no_field_objects():
    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    lowerer = SVToLogicTreeLowerer()
    #module_map = lowerer.lower_sv_text(sv)  # or however you use the lowerer
    module_map = lower_sv_text_to_logic(sv)
    mod = module_map["m"]


    expected = AndOp(BitSelect(LogicVar("s"), 1), NotOp(BitSelect(LogicVar("s"), 0)))
    assert mod.assignments["y"].rhs == expected

    bad_fields = check_for_bad_fields(mod)
    assert not bad_fields, f"Dataclass Field objects found in Module instance: {bad_fields}"

def test_basic_lowering():
    sv = """
    module m(input logic [1:0] s, output logic y);
      assign y = (s == 2'b10);
    endmodule
    """
    lowerer = SVToLogicTreeLowerer()
    #module_map = lowerer.lower_sv_text(sv)  # or however you use the lowerer
    module_map = lower_sv_text_to_logic(sv)
    
    for tree in module_map.values():
        assert_no_fields(tree)
