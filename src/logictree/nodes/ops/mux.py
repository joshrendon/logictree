from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicVar


@dataclass(frozen=True)
class LogicMux(LogicTreeNode):
    """
    A 2:1 multiplexer node in the LogicTree IR.

    - selector: LogicTreeNode (Boolean condition or bit)
    - if_true: LogicTreeNode (value when selector == 1)
    - if_false: LogicTreeNode (value when selector == 0)

    This represents a functional multiplexer, not yet lowered to gates.
    """
    selector: LogicTreeNode
    if_true: LogicTreeNode
    if_false: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def children(self) -> list[LogicTreeNode]:
        return [self.selector, self.if_true, self.if_false]

    @property
    def operands(self):
        return [self.selector, self.if_true, self.if_false]

    def __iter__(self):
        yield from self.children

    def __hash__(self):
        return hash((type(self), self.selector, self.if_true, self.if_false))

    def __eq__(self, other):
        if not isinstance(other, LogicMux):
            return NotImplemented
        return (
            self.selector == other.selector
            and self.if_true == other.if_true
            and self.if_false == other.if_false
        )

    def __str__(self):
        return f"mux({self.selector}, {self.if_true}, {self.if_false})"

    def label(self) -> str:
        return "MUX"

    def free_vars(self) -> FrozenSet[LogicVar]:
        return (
            self.selector.free_vars()
            | self.if_true.free_vars()
            | self.if_false.free_vars()
        )

    #def to_primitives(self) -> LogicTreeNode:
    #    """
    #    Lower to AOI form:
    #      mux(sel, a, b) = (sel AND a) OR (~sel AND b)
    #    """
    #    from logictree.nodes.ops.gates import AndOp, NotOp, OrOp

    #    sel = self.selector
    #    return OrOp(
    #        AndOp(sel, self.if_true),
    #        AndOp(NotOp(sel), self.if_false),
    #    )

    def writes(self) -> set[str]:
        return set()
    
    def writes_must(self) -> set[str]:
        return set()

    def to_sympy_expr(self, var_map=None):
        from sympy import And, Not, Or
        sel = self.selector.to_sympy_expr(var_map)
        t_branch = self.if_true.to_sympy_expr(var_map)
        f_branch = self.if_false.to_sympy_expr(var_map)
        return Or(And(sel, t_branch), And(Not(sel), f_branch))
