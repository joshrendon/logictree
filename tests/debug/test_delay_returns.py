# tests/debug/test_delay_returns.py

import inspect
import warnings
import pytest
from logictree.nodes.registry import all_node_classes
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.ops.gates import (
    AndOp, OrOp, NotOp, XorOp, XnorOp, NandOp
)
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.struct.module import Module
from logictree.nodes.ops.ops import LogicOp
from logictree.nodes.selects import BitSelect, PartSelect, Concat


def test_all_nodes_delay_returns_number():
    failed = []
    skipped = []

    for cls in all_node_classes():
        if cls in (LogicOp, Module):
            continue

        try:
            if cls in (AndOp, OrOp, XorOp, XnorOp, NandOp):
                node = cls(LogicConst(0), LogicConst(1))
            elif cls is NotOp:
                node = NotOp(LogicConst(0))
            elif cls is LogicAssign:
                node = LogicAssign(lhs=LogicVar("out"), rhs=LogicConst(1))
            elif cls is CaseStatement:
                node = CaseStatement(selector=LogicVar("s"), items=[], default=None)
            elif cls is CaseItem:
                node = CaseItem(labels=LogicConst(1), body=LogicConst(42), default=False)
            elif cls is IfStatement:
                node = IfStatement(
                    cond=LogicConst(1),
                    then_branch=LogicConst(2),
                    else_branch=LogicConst(3),
                )
            elif cls is LogicMux:
                node = LogicMux(
                    selector=LogicConst(1),
                    if_true=LogicConst(2),
                    if_false=LogicConst(3),
                )
            elif cls is BitSelect:
                node = BitSelect(base=LogicVar("v"), index=0)
            elif cls is PartSelect:
                node = PartSelect(base=LogicVar("v"), msb=3, lsb=0)
            elif cls is Concat:
                node = Concat(parts=[LogicConst(0), LogicConst(1)])
            elif cls is LogicConst:
                node = LogicConst(0)
            else:
                sig = inspect.signature(cls)
                kwargs = {
                    k: LogicConst(0)
                    for k, v in sig.parameters.items()
                    if v.default is inspect.Parameter.empty and k != "self"
                }
                node = cls(**kwargs) if kwargs else cls()

            if hasattr(node, "delay"):
                value = node.delay
                if callable(value):
                    failed.append(f"{cls.__name__}.delay is a method, not a property")
                elif not isinstance(value, (int, float)):
                    failed.append(f"{cls.__name__}.delay is not int or float: {type(value)}")
            else:
                skipped.append(cls.__name__)

        except Exception as e:
            failed.append(f"{cls.__name__}.delay raised: {repr(e)}")

    for s in skipped:
        warnings.warn(f"{s} has no .delay property")

    assert not failed, "\n".join(failed)
