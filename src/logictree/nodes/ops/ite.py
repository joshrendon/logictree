import logging
from dataclasses import dataclass

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops import LogicOp

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ITEOp(LogicOp):
    cond:     LogicTreeNode
    if_true:  LogicTreeNode
    if_false: LogicTreeNode

    @property
    def children(self):
        return [self.cond, self.if_true, self.if_false]

    @property
    def operands(self):
        return [self.cond, self.if_true, self.if_false]

    @property
    def op(self): return "?:"

    def __str__(self):
        # human-friendly rendering
        return f"ITE({self.cond}, {self.if_true}, {self.if_false})"

    def label(self):
        return f"ite({self.cond.label()}, {self.if_true.label()}, {self.if_false.label()})"

    def to_verilog(self):
        # inline ternary operator ?:
        return f"({self.cond.to_verilog()} ? {self.if_true.to_verilog()} : {self.if_false.to_verilog()})"

    def depth(self): raise NotImplementedError

    def delay(self): raise NotImplementedError

