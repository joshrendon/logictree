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
    def depth(self) -> int:
        inputs = [self.if_true, self.if_false]
        input_depths = [inp.depth for inp in inputs if inp]
        sel_depth = self.selector.depth if self.selector else 0
        return 1 + max(input_depths + [sel_depth], default=0)

    @property
    def delay(self):
        return max(self.if_true.delay, self.if_false.delay, self.selector.delay) + 1

    def label(self) -> str:
        return "MUX"

    def free_vars(self) -> FrozenSet[LogicVar]:
        return (
            self.selector.free_vars()
            | self.if_true.free_vars()
            | self.if_false.free_vars()
        )

    def to_primitives(self) -> LogicTreeNode:
        """
        Lower to AOI form:
          mux(sel, a, b) = (sel AND a) OR (~sel AND b)
        """
        from logictree.nodes.ops.gates import AndOp, NotOp, OrOp

        sel = self.selector
        return OrOp(
            AndOp(sel, self.if_true),
            AndOp(NotOp(sel), self.if_false),
        )
