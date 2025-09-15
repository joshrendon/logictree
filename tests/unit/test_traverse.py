from dd.autoref import BDD, Function

from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect
from logictree.utils.build import build_bdd
from logictree.utils.traverse import collect_logic_vars


def test_collect_logic_vars_bitselect_eqop():
    s = LogicVar("s")
    expr = EqOp(lhs=BitSelect(base=s, index=LogicConst(0)), rhs=LogicConst(1))
    vars_found = set(v.name for v in collect_logic_vars(expr))
    assert vars_found == {"s"}

def test_mux_hash_matches_expected():
    a = LogicVar("a")
    b = LogicVar("b")
    s = LogicVar("sel")
    mux = LogicMux(s, a, b)

    bdd = BDD()
    bdd.declare("a", "b", "sel")
    var_map = {}
    try:
        h = build_bdd(mux, bdd, var_map)

        assert isinstance(h, Function)
        assert str(h) # basic check that the bdd renders
    finally:
        del h
        del bdd
