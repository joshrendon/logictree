from dataclasses import dataclass
from ..base.base import LogicTreeNode
from typing import List, Union, Set

@dataclass
class LogicAssign(LogicTreeNode):
    def __init__(self, lhs: str, rhs: LogicTreeNode):
        self.lhs = lhs
        self.rhs = rhs
    lhs: str
    rhs: LogicTreeNode

    def inputs(self) -> Set[str]:
        print(f"[DEBUG] Calling inputs() on LogicAssign with lhs={self.lhs}")
        return self.rhs.inputs()

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"

