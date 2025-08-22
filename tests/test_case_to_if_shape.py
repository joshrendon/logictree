import pytest
pytestmark = [pytest.mark.unit]

import itertools
from logictree.api import lower_sv_to_logic
from logictree.eval import evaluate                            # simple boolean evaluator

def _assignments(vars_):
    for bits in itertools.product([0,1], repeat=len(vars_)):
        yield dict(zip(vars_, bits))

# tests/test_case_to_if_shape.py
def test_default_maps_to_else_equivalence():
    sv = r"""
    module m(
      input  logic [1:0] s,
      input  logic a,
      input  logic b,
      input  logic c,
      output logic y
    );
      always_comb begin
        case (s)
          2'b00: y = a;
          2'b10: y = b;
          default: y = c;
        endcase
      end
    endmodule
    """
    result = lower_sv_to_logic(sv)
    mod = lower_sv_to_logic(sv)["m"]
    module = result["m"]
    cs = mod.signal_map["y"]
    #print([(it.labels, type(it.labels)) for it in cs.items])
    from logictree.transforms.case_to_if import case_to_if_tree
    lowered_map = case_to_if_tree(module)   # -> {'y': IfStatement}
    assert "y" in lowered_map
    
    # Semantic equivalence over all inputs
    orig_map = dict(module.signal_map)
    vars_ = sorted({n.name for t in orig_map.values() for n in t.free_vars()})

    # Optional: spot-check that default path (s==01 or s==11) resolves to c.
    # Only run if your evaluator exposes s as s[0]/s[1] variables.
    if "s[0]" in vars_ and "s[1]" in vars_:
        for s_val in (1, 3):  # 01, 11
            for a_val in (0, 1):
                for b_val in (0, 1):
                    for c_val in (0, 1):
                        asn = {
                            "s[0]": s_val & 1,
                            "s[1]": (s_val >> 1) & 1,
                            "a": a_val,
                            "b": b_val,
                            "c": c_val,
                        }
                        assert evaluate(lowered_map["y"], asn) == c_val
