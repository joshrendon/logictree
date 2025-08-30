import pytest

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.ops import LogicConst, LogicVar


@pytest.mark.unit
def test_logicvar_init():
    v = LogicVar("a")
    assert v.name == "a"

@pytest.mark.unit
def test_logicconst_init_true():
    c = LogicConst(True)
    assert c.value == 1
    assert c.width == 1

@pytest.mark.unit
def test_notop_init():
    v = LogicVar("x")
    n = NotOp(v)
    assert n.children == [v]

@pytest.mark.unit
def test_andop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = AndOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_orop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = OrOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_xorop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = XorOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_xnorop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = XnorOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_nandop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = NandOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_norop_init():
    a, b = LogicVar("a"), LogicVar("b")
    op = NorOp(a, b)
    assert op.children == [a, b]

@pytest.mark.unit
def test_logicassign_init():
    lhs, rhs = LogicVar("out"), LogicVar("in")
    assign = LogicAssign(lhs, rhs)
    assert assign.lhs == lhs
    assert assign.rhs == rhs

@pytest.mark.unit
def test_ifstatement_init():
    cond, t_branch, f_branch = LogicVar("cond"), LogicVar("t"), LogicVar("f")
    stmt = IfStatement(cond, t_branch, f_branch)
    assert stmt.cond == cond
    assert stmt.then_branch == t_branch
    assert stmt.else_branch == f_branch

@pytest.mark.unit
def test_casestatement_init():
    selector = LogicVar("sel")
    y = LogicVar("y")

    items =  [
            CaseItem(labels=[LogicConst(0)], body=[LogicAssign(lhs=y, rhs=LogicVar("a"))], default=False),
            CaseItem(labels=[LogicConst(1)], body=[LogicAssign(lhs=y, rhs=LogicVar("b"))], default=False)
    ]
    default = CaseItem(labels=[LogicConst("default")], body=[LogicAssign(lhs=y, rhs=LogicVar("c"))], default=True)
    stmt = CaseStatement(selector, items, default)
    assert stmt.selector == selector
    assert stmt.items == items
    assert stmt.default == default
