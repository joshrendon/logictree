import logging

from logictree.nodes.control.assign import LogicAssign, ProceduralAssign
from logictree.nodes.ops.ops import LogicVar
from logictree.pipeline import lower_sv_text_to_logic
from logictree.utils.display import pretty_print

log = logging.getLogger(__name__)


def test_no_operator_nodes_in_signal_map():
    sv = r"""
    module m(input a, b, output y, z);
      assign y = a & b;
      always @* begin
        z = a | b;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    log.info(f"{pretty_print(m)}")

    # No operators should appear in signal_map
    for name, node in m.signal_map.items():
        assert isinstance(node, LogicVar), f"{name} -> {node} is not a LogicVar"

    # Driving logic is in assignments
    assert isinstance(m.get_assignment("y"), LogicAssign)
    z = m.get_procedural_assignment("z")
    log.info(f"z: {z}")

    assert isinstance(m.get_procedural_assignment("z"), ProceduralAssign)

def test_only_vars_and_assigns_in_signal_map():
    sv = """
    module m(input a, b, output y);
      assign y = a & b;
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    for name, node in m.signal_map.items():
        assert isinstance(node, LogicVar), f"{name} -> {node} is not a LogicVar"
