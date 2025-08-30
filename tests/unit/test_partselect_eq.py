import pytest

from logictree.api import lower_sv_to_logic
from logictree.eval import evaluate
from logictree.nodes.struct.module import Module
from tests.utils_bitselect import assert_neq_const_terms

pytestmark = [pytest.mark.unit]


def test_eq_partselect_high_bits():
    sv = """
    module m(input logic [7:0] s, output logic y);
      assign y = (s[7:4] == 4'b1010);
    endmodule
    """
    mod_map = lower_sv_to_logic(sv)
    assert isinstance(mod_map, dict) and "m" in mod_map
    module = mod_map["m"]
    assert isinstance(module, Module)

    # Original outputs map from the module
    #print(f"DEBUG: signal_map: {module.signal_map}")

    # Transform entire module → {signal_name: lowered_node}
    from logictree.transforms.case_to_if import lower_module_cases
    lowered_module = lower_module_cases(module)

    assignments = lowered_module.assignments
    print(f"module: {module}")
    print(f"lowered_module.assignments: {assignments}")
    rhs = module.assignments["y"].rhs

    # Case: s[7:4] = 0b1010 → expect y=1
    env = {f"s[{i}]": (val >> i) & 1 for i, val in [(4, 0b1010), (5, 0), (6, 1), (7, 1)]}
    env.update({f"s[{i}]": 0 for i in range(4)})  # low bits irrelevant
    env["s"] = 0  # placeholder to satisfy LogicVar lookups
    assert evaluate(rhs, env) == 1


def test_eq_partselect_low_bits():
    sv = """
    module m(input logic [3:0] s, output logic y);
      assign y = (s[3:2] == 2'b11);
    endmodule
    """
    module = lower_sv_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs

    # Case: s[3:2] = 2'b11 → expect y=1
    env = {f"s[{i}]": 1 for i in range(4)}
    env["s"] = 0  # placeholder
    assert evaluate(rhs, env) == 1

def test_neq_partselect_high_bits():
    sv = """
    module m(input logic [7:0] s, output logic y);
      assign y = (s[7:4] != 4'b1010);
    endmodule
    """
    module = lower_sv_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs

    assert_neq_const_terms(rhs, 0b1010, 4, "s")

    # Case: s[7:4] == 1010 → expect y=0 (equal, so != is false)
    env_equal = {f"s[{i}]": (0b1010 >> (i - 4)) & 1 for i in range(4, 8)}
    env_equal.update({f"s[{i}]": 0 for i in range(0, 4)})  # irrelevant lower bits
    env_equal["s"] = 0  # placeholder
    assert evaluate(rhs, env_equal) == 0

    # Case: s[7:4] == 1100 → expect y=1 (not equal)
    env_diff = {4: 0, 5: 0, 6: 1, 7: 1}  # 1100
    env_diff = {f"s[{i}]": v for i, v in env_diff.items()}
    env_diff.update({f"s[{i}]": 0 for i in range(0, 4)})
    env_diff["s"] = 0
    assert evaluate(rhs, env_diff) == 1


def test_neq_partselect_low_bits():
    sv = """
    module m(input logic [3:0] s, output logic y);
      assign y = (s[3:2] != 2'b11);
    endmodule
    """
    module = lower_sv_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs

    # Case: s[3:2] == 11 → expect y=0
    env_equal = {f"s[{i}]": 1 for i in range(4)}  # upper bits = 11
    env_equal["s"] = 0
    assert evaluate(rhs, env_equal) == 0

    # Case: s[3:2] == 10 → expect y=1
    env_diff = {0: 0, 1: 0, 2: 0, 3: 1}  # s[3:2] = 10
    env_diff = {f"s[{i}]": v for i, v in env_diff.items()}
    env_diff["s"] = 0
    assert evaluate(rhs, env_diff) == 1
