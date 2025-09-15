from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from logictree.nodes.base.base import LogicTreeNode

if TYPE_CHECKING:
    from logictree.nodes.control.assign import LogicAssign


@dataclass
class Module:
    name: str
    ports: List[str] = field(default_factory=list)
    signal_map: dict[str, LogicTreeNode] = field(default_factory=dict)
    assignments: dict[str, "LogicAssign"] = field(default_factory=dict)
    instances: list = field(default_factory=list)
    vector_widths: dict[str, tuple[int, int]] = field(default_factory=dict)

    def free_vars(self) -> set[str]:
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = set()
        for node in self.signal_map.values():
            if hasattr(node, "free_vars"):
                s |= node.free_vars()
        try:
            # self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return set(s)

    def get_signal(self, name: str) -> LogicTreeNode | None:
        if not isinstance(name, str):
            raise TypeError(f"[BUG] get_signal() called with non-str key: {type(name).__name__}: {name!r}")
        return self.signal_map.get(name)
