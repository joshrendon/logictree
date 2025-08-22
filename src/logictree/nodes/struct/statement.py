from abc import ABC, abstractmethod
from typing import FrozenSet, Optional
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
