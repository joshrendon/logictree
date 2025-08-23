from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Set

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicVar
from logictree.nodes.struct.statement import Statement

log = logging.getLogger(__name__)

@dataclass
class LogicAssign(Statement):
    lhs: LogicVar
    rhs: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)
    annotated_delay: Optional[int] = None

    def __init__(self, lhs: LogicTreeNode, rhs: LogicTreeNode):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    # -- Variable Analysis -----------------------------------------------------
    def free_vars(self) -> FrozenSet[LogicVar]:
        """Variables used in RHS; LHS is not free."""
        if self._free_cache is None:
            self._free_cache = frozenset(self.rhs.free_vars())
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        """LHS is always written."""
        if self._w_cache is None:
            base_lhs = self.lhs.base() if hasattr(self.lhs, "base") else self.lhs
            self._w_cache = frozenset({base_lhs})
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        """Assign always writes (unconditional)."""
        if self._wm_cache is None:
            self._wm_cache = self.writes()
        return self._wm_cache

    # -- Labeling and Stringification -----------------------------------------
    def default_label(self) -> str:
        return f"{self.lhs} = {self.rhs}"

    def __str__(self) -> str:
        return self.default_label()

    # -- Analysis Properties ---------------------------------------------------
    @property
    def depth(self) -> int:
        return getattr(self.rhs, "depth", 0)

    @property
    def delay(self) -> int:
        return self.annotated_delay if self.annotated_delay is not None else getattr(self.rhs, "delay", 0)

    def inputs(self) -> Set[str]:
        return self.rhs.inputs()

    # -- JSON / Visualization Support ------------------------------------------
    def to_json_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "expr_source": str(self.lhs),
            "children": [self.rhs.to_json_dict()],
            "depth": self.depth,
            "delay": self.delay
        }

    # -- Simplification --------------------------------------------------------
    def simplify(self) -> LogicAssign:
        return self

