import pytest

pytestmark = [pytest.mark.unit]


from logictree.pipeline import lower_sv_text_to_logic


def test_mux_tree_outputs_mux():
    sv = """
    module m(input logic s, input logic a, b, output logic y);
      always_comb begin
        case (s)
          1'b0: y = a;
          1'b1: y = b;
        endcase
      end
    endmodule
    """
    module_map = lower_sv_text_to_logic(sv)
    #pprint(module_map)
    mod = module_map["m"]  # Use module name as key
    #pprint(mod)
    y = mod.signal_map["y"]
    #print("mod.signal_map:\n")
    #pprint(mod.signal_map)
    assert y.op == "mux"

