from dataclasses import dataclass
from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List, Set

@dataclass
class LogicAssign(LogicTreeNode):
    def __init__(self, lhs: LogicTreeNode, rhs: LogicTreeNode):
        self.lhs = lhs
        self.rhs = rhs
    lhs: LogicTreeNode
    rhs: LogicTreeNode
    annotated_delay: Optional[int] = None

    def inputs(self) -> Set[str]:
        print(f"[DEBUG] Calling inputs() on LogicAssign with lhs={self.lhs}")
        return self.rhs.inputs()

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"

    @property
    def label(self):
        return f"{self.lhs} ="

    @property
    def depth(self) -> int:
        return getattr(self.rhs, "depth", 0)

    @property
    def delay(self) ->int:
        # placeholder for future gate-delay modeling
        if hasattr(self, "annotated_delay"):
            return self.annotated_delay
        # Default to RHS delay
        return getattr(self.rhs, "delay", 0)


    def to_json_dict(self):
        return {
            "type": "LogicAssign",
            "label": self.label,
            "expr_source": str(self.lhs),
            "children": [self.rhs.to_json_dict()],
            "depth": self.depth,
            "delay": self.delay
        }
    
    def simplify(self):
        return self

