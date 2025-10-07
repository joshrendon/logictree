from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Set, Union

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.statement import Statement

log = logging.getLogger(__name__)

ALLOWED_RHS_TYPES = (
    EqOp, NeqOp,
    AndOp, OrOp, NotOp,
    LogicVar, LogicConst, LogicOp,
    LogicMux, IfStatement, CaseStatement, CaseItem,
    BitSelect, PartSelect, Concat, ITEOp
)


@dataclass(frozen=True)
class LogicAssign(Statement):
    lhs: LogicVar
    rhs: Union[LogicTreeNode, IfStatement]
    blocking: Optional[bool] = None
    annotated_delay: Optional[int] = None
    metadata: Optional[dict] = field(default=None, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "lhs", self._normalize_lhs(self.lhs))
        object.__setattr__(self, "rhs", self._normalize_rhs(self.rhs))

    def _normalize_lhs(self, lhs_node):
        if isinstance(lhs_node, LogicTreeNode):
            return lhs_node 
        if isinstance(lhs_node, str):
            return LogicVar(lhs_node)
        raise TypeError(f"LogicAssign _normalize_lhs() Unsupported lhs type: {type(lhs_node)}")

    def _normalize_rhs(self, rhs_node: LogicTreeNode) -> LogicTreeNode:
        if isinstance(rhs_node, ALLOWED_RHS_TYPES):
            return rhs_node 
        raise TypeError(f"LogicAssign _normalize_rhs() Unsupported rhs type: {type(rhs_node)}")

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

    def inputs(self) -> Set[str]:
        return self.rhs.inputs()

    @property
    def children(self):
        kids: List[LogicTreeNode] = []
        if self.lhs is not None:
            kids.append(self.lhs)
        if self.rhs is not None:
            kids.append(self.rhs)
        return kids

    def pretty_inline(self) -> str:
        """Compact string for debugging or single-line dumps."""
        if self.blocking is None:
            op = "="    # continuous assign
            kind = "assign"
        else:
            op = "=" if self.blocking else "<="
            kind = "proc"
        rhs_str = getattr(self.rhs, "pretty_inline", lambda: str(self.rhs))()
        return f"{kind}:{self.lhs.name} {op} {rhs_str}"

@dataclass(frozen=True)
class ContinuousAssign(LogicAssign):
    """Represents: assign lhs = rhs;"""
    def __post_init__(self):
        object.__setattr__(self, "blocking", None) # enforce distinction


@dataclass(frozen=True)
class ProceduralAssign(LogicAssign):
    """Represents assignments inside always blocks."""
    blocking: bool = True   # = vs <=
    def __post_init__(self):
        # continuous assignments should never sneak in here
        if self.blocking is None:
            raise ValueError("ProceduralAssign requires blocking=True/False")
