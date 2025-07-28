from ..base.base import LogicTreeNode
#from ..ops import LogicOp
from ..ops import LogicOp
from typing import List, Union

class NotOp(LogicOp):
    def __init__(self, operand):
        self.operand = operand
        #super().__init__('NOT', [inputs])
    
    @property
    def op(self):
        return [self.operand]

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
