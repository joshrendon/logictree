from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Set

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicVar
from logictree.nodes.struct.statement import Statement

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LogicAssign(Statement):
    lhs: LogicVar
    rhs: LogicTreeNode
    annotated_delay: Optional[int] = None
    metadata: Optional[dict] = field(default=None, compare=False, repr=False)

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset(self.rhs.free_vars())

    def writes(self) -> FrozenSet[LogicVar]:
        base_lhs = self.lhs.base() if hasattr(self.lhs, "base") else self.lhs
        return frozenset({base_lhs})

    def writes_must(self) -> FrozenSet[LogicVar]:
        return self.writes()

    def target_name(self) -> str:
        return self.lhs.name

    def default_label(self) -> str:
        return f"{str(self.lhs)} = {str(self.rhs)}"

    def __str__(self) -> str:
        return self.default_label()

    @property
    def depth(self) -> int:
        return self.rhs.depth if hasattr(self.rhs, "depth") else 0

    @property
    def delay(self) -> int:
        return (
            self.annotated_delay
            if self.annotated_delay is not None
            else getattr(self.rhs, "delay", 0)
        )

    def inputs(self) -> Set[str]:
        return self.rhs.inputs()

    def to_json_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "expr_source": str(self.lhs),
            "children": [self.rhs.to_json_dict()],
            "depth": self.depth,
            "delay": self.delay,
        }
