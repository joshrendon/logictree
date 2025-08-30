
import pytest
from logictree.utils.serialize import logic_tree_to_json  # optional, if you want to dump on failure
from logictree.pipeline import lower_sv_file_to_logic, lower_sv_text_to_logic
from logictree.nodes import LogicAssign

def assert_all_nodes_have_depth(node, path="root"):
    try:
        _ = node.depth
    except Exception as e:
        raise AssertionError(f"Missing or broken .depth at {path}: {type(node).__name__} → {e}") from e

    for i, child in enumerate(getattr(node, "children", [])):
        if child:
            assert_all_nodes_have_depth(child, path=f"{path}/{type(child).__name__}[{i}]")

@pytest.mark.parametrize("sv_text", [
    # Short SV modules you know are already valid
    """
    module simple(input logic a, b, output logic y);
        assign y = a & b;
    endmodule
    """,
    """
    module mux3(
        input logic [1:0] s,
        input logic a,
        input logic b,
        input logic c,
        output logic y
        );
        always_comb begin
            case (s)
              2'b00: y = a;
              2'b01: y = b;
              default: y = c;
            endcase
        end
    endmodule
    """,
])
def test_all_nodes_have_depth(sv_text):
    module_map = lower_sv_text_to_logic(sv_text)
    for mod in module_map.values():
        for assign in mod.assignments:
            if isinstance(assign, LogicAssign):
                assert_all_nodes_have_depth(assign.rhs)

