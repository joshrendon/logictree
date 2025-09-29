import pytest
from logictree.pipeline import lower_sv_text_to_logic
from logictree.nodes.ops.gates import OrOp, AndOp
from logictree.nodes.ops.ops import LogicVar
from logictree.nodes.control.assign import LogicAssign, ContinuousAssign, ProceduralAssign
from logictree.utils.display import pretty_print
import logging
log = logging.getLogger(__name__)

def test_continuous_assign_lowering():
    sv = "module m(input a, b, output y); assign y = a & b; endmodule"
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]
    assign = m.assignments["y"]
    assert isinstance(assign, ContinuousAssign)
    assert assign.blocking is None


def test_procedural_assign_lowering():
    sv = "module m(input a, b, output z); always @* begin z = a | b; end endmodule"
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]
    assign = m.assignments["z"]
    assert isinstance(assign, ProceduralAssign)
    assert assign.blocking is True
