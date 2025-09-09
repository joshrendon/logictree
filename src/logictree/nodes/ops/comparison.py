"""
Comparison operation nodes.

Defines EqOp (==) and NeqOp (!=) as concrete LogicOp nodes.
These are expression-level operators, not statements: they do not
write signals, they only read them. Each has its own _free_cache
to support repeated free_vars() calls.
"""

from __future__ import annotations

from typing import FrozenSet, Optional
from dataclasses import dataclass

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicOp, LogicVar, LogicConst

@dataclass(frozen=True)
class EqOp(LogicOp):
    """
    Equality operation node: (lhs == rhs).
    """
    lhs: LogicTreeNode | str | int
    rhs: LogicTreeNode | str | int
    _free_cache: Optional[FrozenSet[LogicVar]] = None

    def __post_init__(self):
        object.__setattr__(self, "lhs", self._normalize(self.lhs))
        object.__setattr__(self, "rhs", self._normalize(self.rhs))

    @property
    def children(self):
        return list(self.operands)

    @property
    def op(self) -> str:
        return "EQ"

    @property
    def operands(self):
        # Satisfy LogicOp’s abstract API and __repr__
        return (self.lhs, self.rhs)

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

    def pretty_inline(self):
        return str(self)

    def label(self) -> str:
        return f"{self.lhs.label()} == {self.rhs.label()}"

    def pretty_label(self) -> str:
        lhs, rhs = self.operands
        return f"{lhs} == {rhs}"


@dataclass(frozen=True)
class NeqOp(LogicOp):
    """
    Inequality operation node: (lhs != rhs).
    """
    lhs: LogicTreeNode | str | int
    rhs: LogicTreeNode | str | int

    _free_cache: Optional[FrozenSet[LogicVar]] = None

    def __post_init__(self):
        object.__setattr__(self, "lhs", self._normalize(self.lhs))
        object.__setattr__(self, "rhs", self._normalize(self.rhs))

    @property
    def children(self):
        return list(self.operands)

    @property
    def op(self) -> str:
        return "NEQ"

    @property
    def operands(self):
        return (self.lhs, self.rhs)

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

    def pretty_inline(self):
        return str(self)

    def label(self) -> str:
        return f"{self.lhs.label()} != {self.rhs.label()}"

    def pretty_label(self) -> str:
        lhs, rhs = self.operands
        return f"{lhs} != {rhs}"


__all__ = ["EqOp", "NeqOp"]
