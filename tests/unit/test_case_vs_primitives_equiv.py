from logictree.nodes.control.assign import LogicAssign
from logictree.pipeline import lower_sv_text_to_logic
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.if_to_mux import if_to_mux_tree
from logictree.transforms.to_primitives import to_primitives_logic_tree
from logictree.utils.assertion import assert_logic_equiv, exhaustive_input_equiv


def test_case_vs_primitives_equiv():
    verilog_text = """
    module mux_case(input logic sel, a, b, output logic out);
      always_comb begin
        case(sel)
          1'b0: out = a;
          1'b1: out = b;
        endcase
      end
    endmodule
    """

    # Parse and lower
    module_map = lower_sv_text_to_logic(verilog_text)
    mod = module_map["mux_case"]

    top_assign = mod.assignments["out"]
    assert isinstance(top_assign, LogicAssign)

    # Lower: case → if
    if_tree = case_to_if_tree(top_assign.rhs)
    assert if_tree is not None
    assert hasattr(if_tree, "cond")

    # Lower: if → mux
    mux_tree = if_to_mux_tree(if_tree)

    # Build two assignment trees: one from case→mux, one from case→mux→primitives
    mux_assign = LogicAssign(lhs=top_assign.lhs, rhs=mux_tree)
    prim_assign = LogicAssign(lhs=top_assign.lhs, rhs=to_primitives_logic_tree(mux_tree))

    # Will raise AssertionError if not equivalent
    assert_logic_equiv(mux_assign, prim_assign)

def test_case_vs_primitives_exhaustive():
    verilog_text = """
    module mux_case(input logic sel, a, b, output logic out);
      always_comb begin
        case(sel)
          1'b0: out = a;
          1'b1: out = b;
        endcase
      end
    endmodule
    """

    # Parse and lower
    module_map = lower_sv_text_to_logic(verilog_text)
    mod = module_map["mux_case"]

    top_assign = mod.assignments["out"]
    assert isinstance(top_assign, LogicAssign)

    # Lower: case → if
    if_tree = case_to_if_tree(top_assign.rhs)
    assert if_tree is not None
    assert hasattr(if_tree, "cond")

    # Lower: if → mux
    mux_tree = if_to_mux_tree(if_tree)

    # Build two assignment trees: one from case→mux, one from case→mux→primitives
    mux_assign = LogicAssign(lhs=top_assign.lhs, rhs=mux_tree)

    # ... lower Verilog to mux_tree and prim_tree like before
    mux_assign = LogicAssign(lhs=top_assign.lhs, rhs=mux_tree)
    prim_assign = LogicAssign(lhs=top_assign.lhs, rhs=to_primitives_logic_tree(mux_tree))

    # Input variable names: depends on your module
    inputs = ["sel", "a", "b"]

    assert exhaustive_input_equiv(mux_assign, prim_assign, inputs)
