import logging

import pytest

pytestmark = [pytest.mark.integration]
log = logging.getLogger(__name__)

import itertools
import types

from logictree.api import lower_sv_to_logic
from logictree.eval import evaluate  # simple boolean evaluator
from logictree.transforms.case_to_if import case_to_if_tree, transform_cases
from logictree.utils.display import pretty_print


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
    orig_map = lower_sv_to_logic(sv)
    module = orig_map["m"]
    log.info(f"module: type: {type(module).__name__}\n{pretty_print(module)}")

    assignments = module.assignments
    #assert orig_map.default is not None
    log.info(f"assignments:\npretty_print{assignments}")

    for assign in module.get_assignments():
        log.info(f"assign: {assign}")

    
    #print("DBG case_to_if_tree:", case_to_if_tree, type(case_to_if_tree))
    assert isinstance(case_to_if_tree, types.FunctionType), (
        "shadowed by", type(case_to_if_tree), "value:", case_to_if_tree
    )
    
    assert callable(case_to_if_tree), type(case_to_if_tree)
    lowered = {k: transform_cases(v) for k, v in orig_map.items()}

    for k,v in lowered.items():
        log.debug(f"lowered: {k} {pretty_print(v)}")

    vars_ = sorted({n.name for t in orig_map.values() for n in t.free_vars()})
    # vars_ should include s, a, b, c
    assert len(vars_) <= 8
    for asn in _assignments(vars_):
        for net in orig_map:
            assert evaluate(orig_map[net], asn) == evaluate(lowered[net], asn)
