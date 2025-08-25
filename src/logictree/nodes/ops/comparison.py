"""
Comparison operation nodes.

Defines EqOp (==) and NeqOp (!=) as concrete LogicOp nodes.
These are expression-level operators, not statements: they do not
write signals, they only read them. Each has its own _free_cache
to support repeated free_vars() calls.
"""

from __future__ import annotations

from typing import FrozenSet, Optional

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicOp, LogicVar


class EqOp(LogicOp):
    """
    Equality operation node: (lhs == rhs).
    """

    _free_cache: Optional[FrozenSet[LogicVar]] = None

    def __init__(self, lhs: LogicTreeNode, rhs: LogicTreeNode):
        super().__init__(lhs, rhs)
        self.lhs = lhs
        self.rhs = rhs

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is not None:
            return self._free_cache
        vars_ = set(self.lhs.free_vars()) | set(self.rhs.free_vars())
        self._free_cache = frozenset(vars_)
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def writes_must(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def __str__(self):
        return f"({self.lhs} == {self.rhs})"

    def label(self) -> str:
        return "=="

    @property
    def op(self) -> str:
        return "=="


class NeqOp(LogicOp):
    """
    Inequality operation node: (lhs != rhs).
    """

    _free_cache: Optional[FrozenSet[LogicVar]] = None

    def __init__(self, lhs: LogicTreeNode, rhs: LogicTreeNode):
        super().__init__(lhs, rhs)
        self.lhs = lhs
        self.rhs = rhs

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is not None:
            return self._free_cache
        vars_ = set(self.lhs.free_vars()) | set(self.rhs.free_vars())
        self._free_cache = frozenset(vars_)
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def writes_must(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def __str__(self):
        return f"({self.lhs} != {self.rhs})"

    def label(self) -> str:
        return "!="

    @property
    def op(self) -> str:
        return "!="

__all__ = ["EqOp", "NeqOp"]
