import pytest

from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.transforms.if_to_ite import reduce_if_to_ite
from logictree.nodes.ops.ite import ITE


def test_simple_if_else_to_ite():
    # if (sel) y = a; else y = b;
    stmt = IfStatement(
        cond=LogicVar("sel"),
        then_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a")),
        else_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("b"))
    )

    lowered = reduce_if_to_ite(stmt)

    assert isinstance(lowered, LogicAssign)
    assert isinstance(lowered.rhs, ITE)
    assert lowered.lhs == LogicVar("y")
    assert lowered.rhs.if_true == LogicVar("a")
    assert lowered.rhs.if_false == LogicVar("b")


def test_else_if_chain_to_nested_ite():
    # if (c1) y = v1;
    # else if (c2) y = v2;
    # else y = v3;
    stmt = IfStatement(
        cond=LogicVar("c1"),
        then_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("v1")),
        else_branch=IfStatement(
            cond=LogicVar("c2"),
            then_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("v2")),
            else_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("v3"))
        )
    )

    lowered = reduce_if_to_ite(stmt)

    # Top level should be y = ITE(c1, v1, ...)
    assert isinstance(lowered, LogicAssign)
    assert lowered.lhs == LogicVar("y")
    top_ite = lowered.rhs
    assert isinstance(top_ite, ITE)
    assert top_ite.cond == LogicVar("c1")
    assert top_ite.if_true == LogicVar("v1")

    # False branch should itself be an ITE(c2, v2, v3)
    nested = top_ite.if_false
    assert isinstance(nested, ITE)
    assert nested.cond == LogicVar("c2")
    assert nested.if_true == LogicVar("v2")
    assert nested.if_false == LogicVar("v3")


def test_no_else_defaults_to_const0():
    # if (sel) y = a;
    stmt = IfStatement(
        cond=LogicVar("sel"),
        then_branch=LogicAssign(lhs=LogicVar("y"), rhs=LogicVar("a")),
        else_branch=None
    )

    lowered = reduce_if_to_ite(stmt)

    assert isinstance(lowered, LogicAssign)
    assert isinstance(lowered.rhs, ITE)
    assert lowered.rhs.if_false == LogicConst(0)
