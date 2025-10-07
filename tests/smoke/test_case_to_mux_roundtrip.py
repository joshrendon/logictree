import logging

import pytest

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicVar
from logictree.pipeline import lower_sv_text_to_logic
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.if_to_mux import if_to_mux_tree
from logictree.utils.assertion import (
    assert_mux_has_conditions,
    assert_mux_has_leaves,
    assert_mux_path_depth,
    collect_mux_conditions,
    collect_mux_leaf_labels,
)
from logictree.utils.display import multi_branch_mux_pretty_print
from logictree.utils.verilog_emitter import mux_chain_to_verilog_expr

log = logging.getLogger(__name__)


@pytest.mark.smoke
def test_case_to_mux_roundtrip():
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

    log.debug(f"module: mux_case: {mod}")
    # Confirm assignment exists
    assert "out" in mod.assignments
    top_assign = mod.assignments["out"]
    log.debug(f"top_assign: {top_assign}")
    assert isinstance(top_assign, LogicAssign)

    # Lower: case → if
    if_tree = case_to_if_tree(top_assign.rhs)
    assert if_tree is not None
    assert hasattr(if_tree, "cond")

    # Lower: if → mux
    mux_tree = if_to_mux_tree(if_tree)
    mux_assign = LogicAssign(lhs=top_assign.lhs, rhs=mux_tree)
    from logictree.utils.display import pretty_print
    print("Final lowered mux tree:")
    print(pretty_print(mux_assign))
    assert isinstance(mux_assign, LogicAssign)
    mux = mux_assign.rhs
    log.info("multi_branch:")
    log.info(multi_branch_mux_pretty_print(mux))
    log.info("mux_chain_to_verilog_expr:")
    log.info(mux_chain_to_verilog_expr(mux))
    assert isinstance(mux, LogicMux)

    # Structural assertions
    assert mux.selector.label() == "sel == 1'b0" or mux.selector.label() == "sel == 1'b1"
    assert isinstance(mux.if_true, LogicVar)

    # Utility: drill down mux chain to final if_false
    tail = mux
    while isinstance(tail.if_false, LogicMux):
        tail = tail.if_false
    
    # Final check on tail of chain
    assert isinstance(tail.if_false, EmptyBranch)
    mux_leaf_labels = sorted(collect_mux_leaf_labels(mux))
    mux_conditions = sorted(collect_mux_conditions(mux))
    log.info(f"mux_leaf_labels: {mux_leaf_labels}")
    log.info(f"mux_conditions: {mux_conditions}")
    assert_mux_has_leaves(mux, {"a", "b", "<empty>"})
    assert_mux_has_conditions(mux, {"sel == 1'b0", "sel == 1'b1"})
    assert_mux_path_depth(mux, 2)
