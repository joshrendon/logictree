from dataclasses import dataclass
from sympy import ITE as SympyITE
from logictree.nodes.base.base import LogicTreeNode
import logging


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ITEOp(LogicTreeNode):
    cond:     LogicTreeNode
    if_true:  LogicTreeNode
    if_false: LogicTreeNode

    @property
    def children(self):
        return [self.cond, self.if_true, self.if_false]

    def operands(self):
        return [self.cond, self.if_true, self.if_false]

    def __str__(self):
        # human-friendly rendering
        return f"ITE({self.cond}, {self.if_true}, {self.if_false})"

    def label(self):
        # used in DOT/graphviz display
        return "ITE"

    def label(self):
        return f"ite({self.cond.label()}, {self.if_true.label()}, {self.if_false.label()})"

    def to_sympy_expr(self):
        return SympyITE(
            self.cond.to_sympy_expr(),
            self.if_true.to_sympy_expr(),
            self.if_false.to_sympy_expr()
        )


    def to_sympy(self):
        from sympy import Piecewise, true
        return Piecewise(
            (self.if_true.to_sympy(), self.cond.to_sympy()),
            (self.if_false.to_sympy(), true)
        )

    def to_verilog(self):
        # inline ternary operator ?:
        return f"({self.cond.to_verilog()} ? {self.if_true.to_verilog()} : {self.if_false.to_verilog()})"

    def gate_count(self):
        # Roughly: 2 ANDs + 1 OR + cond NOT = ~4 gates
        return 4 + sum(op.gate_count() for op in self.operands())

