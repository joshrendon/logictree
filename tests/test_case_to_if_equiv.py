import itertools
import types
from logictree.api import lower_sv_to_logic
from logictree.nodes.struct.module import Module
from logictree.eval import evaluate

def _assignments(vars_):
    for bits in itertools.product([0,1], repeat=len(vars_)):
        yield dict(zip(vars_, bits))

def test_case_to_if_define_equivalence_mux2_with_default():
    sv = """
    module m(
      input  logic a,
      input  logic b,
      input  logic c,
      input  logic s,
      output logic out
    );
      always_comb begin
        case (s)
          1'b0: out = a;
          1'b1: out = b;
          default: out = c;
        endcase
      end
    endmodule
    """
    # Expect {'m': Module(...)}
    result = lower_sv_to_logic(sv)
    mod = lower_sv_to_logic(sv)["m"]
    cs = mod.signal_map["out"]
    print([(it.labels, type(it.labels)) for it in cs.items])
    assert isinstance(result, dict) and "m" in result
    module = result["m"]
    assert isinstance(module, Module)

    # Original outputs map from the module
    orig_map = dict(module.signal_map)
    print(f"DEBUG: signal_map: {module.signal_map}")

    # Transform entire module → {signal_name: lowered_node}
    from logictree.transforms.case_to_if import case_to_if_tree
    assert isinstance(case_to_if_tree, types.FunctionType) and callable(case_to_if_tree)
    lowered_map = case_to_if_tree(module)
    assert isinstance(lowered_map, dict) and "out" in lowered_map

    # Inputs from original outputs (works with method- or set-style free_vars)
    def _free_vars_of(node):
        fv = getattr(node, "free_vars", None)
        if fv is None:
            return set()
        return set(fv()) if callable(fv) else set(fv)
    for name, node in orig_map.items():
        fv = getattr(node, "free_vars", None)
        if fv is None:
            print(f"[free_vars] {name}: MISSING")
        elif callable(fv):
            try:
                vals = fv()
                print(f"[free_vars] {name}: METHOD -> {sorted(vals)}")
            except Exception as e:
                print(f"[free_vars] {name}: METHOD RAISED {type(e).__name__}: {e}")
        else:
            print(f"[free_vars] {name}: ATTRIBUTE {type(fv).__name__} -> {sorted(fv)}")

    #vars_ = sorted({n for node in orig_map.values() for n in _free_vars_of(node)})
    #vars_ = sorted(orig_map["out"].free_vars(), key=lambda v: v.name)
    vars_ = sorted({n.name for t in orig_map.values() for n in t.free_vars()})
    assert len(vars_) <= 8

    # Compare only nets present in both maps (should include 'out')
    common = set(orig_map) & set(lowered_map)
    assert common

    for asn in _assignments(vars_):
        for net in common:
            print(f"orig_map[{net}] = {orig_map[net]}")
            print(f"lowered_map[{net}] = {lowered_map[net]}")
            assert evaluate(orig_map[net], asn) == evaluate(lowered_map[net], asn)
#from logictree.api import lower_sv_to_logic
#from logictree.transforms.case_to_if import case_to_if_tree
#from logictree.nodes.struct.module import Module
#from logictree.eval import evaluate
#import itertools, types
#
#def _assignments(vars_):
#    for bits in itertools.product([0, 1], repeat=len(vars_)):
#        yield dict(zip(vars_, bits))
#
#def _free_vars_of(node):
#    fv = getattr(node, "free_vars", None)
#    if fv is None:
#        return set()
#    return set(fv()) if callable(fv) else set(fv)
#
#def test_case_to_if_define_equivalence_mux2_with_default():
#    sv = """
#    module m(
#      input  logic a,
#      input  logic b,
#      input  logic c,
#      input  logic s,
#      output logic out
#    );
#      always_comb begin
#        case (s)
#          1'b0: out = a;
#          1'b1: out = b;
#          default: out = c;
#        endcase
#      end
#    endmodule
#    """
#
#    # Expect {'m': Module(...)}
#    result = lower_sv_to_logic(sv)
#    assert isinstance(result, dict) and "m" in result
#    module = result["m"]
#    assert isinstance(module, Module)
#
#    # Original outputs map from the module
#    orig_map = dict(module.signal_map)
#
#    # Lower entire module → {signal_name: lowered_node}
#    assert isinstance(case_to_if_tree, types.FunctionType) and callable(case_to_if_tree)
#    lowered_map = case_to_if_tree(module)
#    assert isinstance(lowered_map, dict)
#
#    for name, node in orig_map.items():
#        fv = getattr(node, "free_vars", None)
#        if fv is None:
#            print(f"[free_vars] {name}: MISSING")
#        elif callable(fv):
#            try:
#                vals = fv()
#                print(f"[free_vars] {name}: METHOD -> {sorted(vals)}")
#            except Exception as e:
#                print(f"[free_vars] {name}: METHOD RAISED {type(e).__name__}: {e}")
#        else:
#            print(f"[free_vars] {name}: ATTRIBUTE {type(fv).__name__} -> {sorted(fv)}")
#
#    # Input vars from original outputs (works whether free_vars is a method or a set)
#    vars_ = sorted({n for node in orig_map.values() for n in _free_vars_of(node)})
#    assert len(vars_) <= 6
#
#    # Compare only common nets (should at least include 'out')
#    common = set(orig_map) & set(lowered_map)
#    assert common
#
#    for asn in _assignments(vars_):
#        for net in common:
#            assert evaluate(orig_map[net], asn) == evaluate(lowered_map[net], asn)
#
