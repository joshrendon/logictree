import pytest
pytestmark = [pytest.mark.unit]

from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from logictree.nodes.ops import LogicVar, AndOp
from logictree.nodes.control.assign import LogicAssign

def test_signal_assignment():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    module_map = lower_sv_text_to_logic(code)
    mod = module_map["foo"]
    assert "b" in mod.signal_map
    assert isinstance(mod.signal_map["b"], LogicVar)
    assert mod.signal_map["b"].name == "b"

def test_simple_assign_is_tracked():
    sv = """
    module foo(input logic a, output logic b);
      assign b = a;
    endmodule
    """
    mod_map = lower_sv_text_to_logic(sv)
    mod = mod_map["foo"]
    assert isinstance(mod.assignments["b"], LogicAssign)
    assert mod.assignments["b"].lhs.name == "b"
    assert mod.assignments["b"].rhs.name == "a"

def test_simple_assign_and():
    sv = """
    module foo(input logic a, input logic b, output logic c);
      assign c = (a & b);
    endmodule
    """
    mod_map = lower_sv_text_to_logic(sv)
    mod = mod_map["foo"]
    assert isinstance(mod.assignments["c"], LogicAssign)
    assert mod.assignments["c"].lhs.name == "c"

    assign = mod.assignments["c"]
    assert isinstance(assign.rhs, AndOp)
    #print(f"DEBUG: AndOp: {assign.rhs}")
    andop = assign.rhs

    #print(f"DEBUG: AndOp.right.name: {andop.right.name}")
    #print(f"DEBUG: AndOp.left.name:  {andop.left.name}")
    #print(f"DEBUG: AndOp.op:  {andop.op}")
    assert andop.right.name == "b"
    assert andop.left.name  == "a"
    assert andop.op == 'AND'
