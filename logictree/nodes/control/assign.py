from dataclasses import dataclass, field
from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List, Set
import logging
log = logging.getLogger(__name__)

@dataclass
class LogicAssign(LogicTreeNode):
    def __init__(self, lhs: LogicTreeNode, rhs: LogicTreeNode):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs
    lhs: str | LogicTreeNode
    rhs: LogicTreeNode
    annotated_delay: Optional[int] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    # LHS is the sink, not an input var; only RHS contributes
    def free_vars(self) -> set[str]:
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = self.rhs.free_vars()
        try:
            #self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return set(s)

    def inputs(self) -> Set[str]:
        log.debug(f"Calling inputs() on LogicAssign with lhs={self.lhs}")
        return self.rhs.inputs()

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"

    def default_label(self):
        return f"{self.lhs} = {self.rhs}"

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
            "type": self.__class__.__name__,
            "label": self.label(),
            "expr_source": str(self.lhs),
            "children": [self.rhs.to_json_dict()],
            "depth": self.depth,
            "delay": self.delay
        }
    
    def simplify(self):
        return self

