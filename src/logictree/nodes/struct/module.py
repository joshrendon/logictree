from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.alwaysblock import AlwaysBlock
from logictree.nodes.ops.ops import LogicVar

if TYPE_CHECKING:
    from logictree.nodes.control.assign import LogicAssign


@dataclass
class Module:
    name: str
    ports: List[str] = field(default_factory=list)
    signal_map: dict[str, LogicTreeNode] = field(default_factory=dict)
    assignments: dict[str, "LogicAssign"] = field(default_factory=dict)
    always_blocks: List[AlwaysBlock] = field(default_factory=list)
    instances: list = field(default_factory=list)
    vector_widths: dict[str, tuple[int, int]] = field(default_factory=dict)

    def __repr__(self):
        return f"Module {self.name} ports={len(self.ports)} assigns={len(self.assignments)} always={len(self.always_blocks)}"

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

    def validate_signal_map(self) -> None:
        """
        Enforce invariant: signal_map values must be *signal-like*,
        never raw operator nodes.
        """
        for k, v in self.signal_map.items():
            if not isinstance(k, str):
                raise TypeError(f"[BUG] signal_map key must be str, got {type(k).__name__}: {k!r}")
            if not isinstance(v, LogicVar):
                raise TypeError(
                    f"[BUG] signal_map value must be LogicVar, got {type(v).__name__}: {v!r}"
                )

    def get_assignment(self, name: str) -> Optional["LogicAssign"]:
        return self.assignments.get(name)

    def get_assignments(self) -> List["LogicAssign"]:
        return list(self.assignments.values())

    def get_always_comb(self) -> List["AlwaysBlock"]:
        return [a for a in self.always_blocks if a.kind.name.lower() == "comb"]

    def get_signals(self) -> List["LogicVar"]:
        return list(self.signal_map.values())

    def get_procedural_assignment(self, name: str) -> Optional["LogicAssign"]:
        """
        Return the first LogicAssign within any always block that drives `name`.
        Searches recursively through nested BlockStatements and control structures.
        Returns None if not found.
        """
        from logictree.nodes.control.assign import LogicAssign
        from logictree.nodes.struct.statement import BlockStatement

        found_assign: Optional["LogicAssign"] = None

        def search_block(block):
            nonlocal found_assign
            if found_assign is not None or block is None:
                return

            # Direct LogicAssign
            if isinstance(block, LogicAssign):
                if getattr(block.lhs, "name", None) == name:
                    found_assign = block
                return

            # BlockStatement: iterate over sub-statements
            if isinstance(block, BlockStatement):
                for stmt in getattr(block, "statements", []):
                    search_block(stmt)
                    if found_assign:
                        return

            # If-like nodes with then/else branches
            for branch in (getattr(block, "then_branch", None),
                           getattr(block, "else_branch", None)):
                search_block(branch)
                if found_assign:
                    return

        for ab in getattr(self, "always_blocks", []):
            search_block(getattr(ab, "body", None))
            if found_assign:
                break

        return found_assign
