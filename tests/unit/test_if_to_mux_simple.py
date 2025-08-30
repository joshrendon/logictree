import pytest

from logictree.nodes import LogicMux, LogicVar
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.transforms.if_to_mux import if_to_mux_tree
from logictree.utils.output import write_dot_to_file

pytestmark = [pytest.mark.unit]

def test_if_to_mux_lowering_simple():
    a, b, sel = LogicVar("a"), LogicVar("b"), LogicVar("sel")

    if_tree = IfStatement(
        cond=sel,
        then_branch=[LogicAssign(lhs=LogicVar("y"), rhs=a)],
        else_branch=[LogicAssign(lhs=LogicVar("y"), rhs=b)],
    )

    mux_tree = if_to_mux_tree(if_tree)

    # Sanity: root should be a MuxOp (or equivalent node)
    assert isinstance(mux_tree, LogicAssign)
    assert isinstance(mux_tree.rhs, LogicMux)
    assert mux_tree.rhs.label().startswith("MUX"), f"Unexpected root {mux_tree}"
    # Verify branches
    assert {v.name for v in mux_tree.free_vars()} == {"a", "b", "sel"}


def test_if_to_mux_viz(tmp_path):
    a, b, sel = LogicVar("a"), LogicVar("b"), LogicVar("sel")
    if_tree = IfStatement(
        cond=sel,
        then_branch=[LogicAssign(lhs=LogicVar("y"), rhs=a)],
        else_branch=[LogicAssign(lhs=LogicVar("y"), rhs=b)],
    )
    mux_tree = if_to_mux_tree(if_tree)

    out_file = tmp_path / "mux.dot"
    write_dot_to_file(mux_tree, filepath=out_file)
    assert out_file.exists()
    assert out_file.read_text().startswith("digraph")
