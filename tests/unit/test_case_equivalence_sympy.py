from logictree.pipeline import lower_sv_text_to_logic
from logictree.utils.assertion import assert_case_equivalence


def test_case_equivalence_sympy():
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

    module_map = lower_sv_text_to_logic(verilog_text)
    mod = module_map["mux_case"]

    case_stmt = mod.assignments["out"].rhs
    assert_case_equivalence(case_stmt)
