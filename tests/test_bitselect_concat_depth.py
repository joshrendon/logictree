from logictree.nodes import BitSelect, Concat, LogicConst, LogicVar, PartSelect


def test_bitselect_concat_depth():
    # Replace with a real parse if needed
    tree = Concat(children=[
        BitSelect(var=LogicVar("x"), index=LogicConst(0)),
        PartSelect(var=LogicVar("y"), msb=LogicConst(3), lsb=LogicConst(0)),
    ])
    assert tree.depth == 1  # since LogicConst.depth = 0, LogicVar.depth = 0 → all depth = 1
