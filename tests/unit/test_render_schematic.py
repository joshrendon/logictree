import pytest
from pathlib import Path

from logictree.nodes.ops.ops import LogicVar
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp
from logictree.utils.schematic import render_schematic
import logging

log = logging.getLogger(__name__)

@pytest.mark.unit
def test_render_schematic_simple(tmp_path: Path):
    """
    Construct a small Boolean circuit:
        y = (a & b) | (~c)
    and render it as a schematic.
    """

    a, b, c = LogicVar("a"), LogicVar("b"), LogicVar("c")

    # Build: (a AND b) OR (NOT c)
    node = OrOp(AndOp(a, b), NotOp(c))

    outfile = tmp_path / "simple_schematic.png"
    path = render_schematic(node, outfile)

    log.info(f"tmp_path: {outfile}")

    # Ensure the file was created and is non-empty
    assert path.exists(), "Schematic file was not created"
    assert path.stat().st_size > 0, "Schematic file is empty"
