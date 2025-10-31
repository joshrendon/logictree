from logictree.analysis.depth import depth
from logictree.nodes import BitSelect, Concat, LogicConst, LogicVar, PartSelect


def test_bitselect_concat_depth():
    # Replace with a real parse if needed
    tree = Concat(parts=[
        BitSelect(base=LogicVar("x"), index=LogicConst(0)),
        PartSelect(base=LogicVar("y"), msb=LogicConst(3), lsb=LogicConst(0)),
    ])
    # Concat/BitSelect/PartSelect are all wire-ops they don't contribute to gate delay modeling (depth), so
    # the test should check that the depth is indeed 0.
    assert depth(tree) == 0  # since LogicConst.depth = 0, LogicVar.depth = 0 → all depth = 0
