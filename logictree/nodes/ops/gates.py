from ..base.base import LogicTreeNode
from ..ops import LogicOp
from typing import List, Union

class NotOp(LogicOp):
    def __init__(self, operand):
        super().__init__()
        self.operand = operand
    
    @property
    def op(self):
        return [self.operand]

    def default_label(self):
        return "NOT"

    @property
    def children(self):
        return [self.operand]
    
    def simplify(self):
        simplified_operand = self.operand.simplify()

        # Double negations: ~~A -> A
        if isinstance(simplified_operand, NotOp):
            return simplified_operand.operand

        return NotOp(simplified_operand)

    def equals(self, other):
        return isinstance(other, NotOp) and self.operand.equals(other.operand)

    def __str__(self):
        return f"(~{self.operand})"

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            "expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }
