from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional

from logictree.nodes.ops.ops import LogicVar


class Statement(ABC):
    """
    Abstract base class for all control-flow or assignment-level statement nodes
    in the LogicTree IR. Implements shared caching and interface contracts for
    free_vars(), writes(), and writes_must().
    """

    # Optional cached values — subclasses can choose to use them
    _free_cache: Optional[FrozenSet[LogicVar]] = None
    _w_cache: Optional[FrozenSet[LogicVar]] = None
    _wm_cache: Optional[FrozenSet[LogicVar]] = None

    def _invalidate_rw_caches(self):
        """Clear any cached results for free_vars(), writes(), writes_must()."""
        self._free_cache = None
        self._w_cache = None
        self._wm_cache = None

    @abstractmethod
    def free_vars(self) -> FrozenSet[LogicVar]:
        """Returns all LogicVars read (free variables) in this statement."""
        ...

    @abstractmethod
    def writes(self) -> FrozenSet[LogicVar]:
        """Returns all LogicVars written to (may-write set)."""
        ...

    @abstractmethod
    def writes_must(self) -> FrozenSet[LogicVar]:
        """Returns all LogicVars written to on all paths (must-write set)."""
        ...


@dataclass(frozen=True)
class BlockStatement(Statement):
    """A sequence of multiple statements grouped as a single statement node."""

    statements: List[Statement] = field(default_factory=list)

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset().union(*(s.free_vars() for s in self.statements))

    def writes(self) -> FrozenSet[LogicVar]:
        return frozenset().union(*(s.writes() for s in self.statements))

    def writes_must(self) -> FrozenSet[LogicVar]:
        # only vars written in *all* child statements
        if not self.statements:
            return frozenset()
        must_sets = [s.writes_must() for s in self.statements]
        return frozenset.intersection(*must_sets)
