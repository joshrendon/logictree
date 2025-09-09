from logictree.nodes.ops.mux import LogicMux
from logictree.utils.build import build_bdd
from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.selects import BitSelect
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp
from logictree.utils.traverse import collect_logic_vars

def test_if_statement_is_assignable():
    cond = LogicVar(name="sel")
    a = LogicVar(name="a")
    b = LogicVar(name="b")

    assign_a = LogicAssign(lhs=LogicVar("out"), rhs=a)
    assign_b = LogicAssign(lhs=LogicVar("out"), rhs=b)

    if_stmt = IfStatement(cond=cond, then_branch=assign_a, else_branch=assign_b)

    assign = LogicAssign(lhs=LogicVar("out"), rhs=if_stmt)

    assert assign.rhs == if_stmt
    assert isinstance(assign.rhs, IfStatement)
