from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.ops import LogicVar


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
