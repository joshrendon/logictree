from dataclasses import dataclass
from sympy import ITE as SympyITE
from logictree.nodes.base.base import LogicTreeNode
import logging


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ITE(LogicTreeNode):
    cond:     LogicTreeNode
    if_true:  LogicTreeNode
    if_false: LogicTreeNode

    def children(self):
        return [self.cond, self.if_true, self.if_false]

    def label(self):
        return f"ite({self.cond.label()}, {self.if_true.label()}, {self.if_false.label()})"

    def depth(self):
        return 1 + max(c.depth() for c in self.children())

    def to_sympy_expr(self):
        return SympyITE(
            self.cond.to_sympy_expr(),
            self.if_true.to_sympy_expr(),
            self.if_false.to_sympy_expr()
        )
