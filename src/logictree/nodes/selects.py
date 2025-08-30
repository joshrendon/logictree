from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops import LogicVar


@dataclass(frozen=True)
class BitSelect(LogicTreeNode):
    """
    Represents a single-bit selection: base[index]
    Example: s[3]
    """

    base: LogicTreeNode
    index: int
    width: int = field(init=False, default=1, repr=False)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "width", 1)

    @property
    def depth(self) -> int:
        return 1 + self.base.depth if self.base else 0

    @property
    def delay(self):
        if hasattr(self.base, "delay"):
            return self.base.delay + 1  # one extra step for indexing
        return 1  # minimum delay

    def equals(self, other: "LogicTreeNode") -> bool:
        return (
            isinstance(other, BitSelect)
            and self.index == other.index
            and self.base.equals(other.base)
        )

    def __repr__(self) -> str:
        return f"{self.base}[{self.index}]"

    def default_label(self) -> str:
        return str(self)

    def set_viz_label(self, label: str) -> None:
        object.__setattr__(self, "_viz_label", label)

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset({self.base})

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, BitSelect)
            and self.base == other.base
            and self.index == other.index
        )

    def __hash__(self) -> int:
        return hash((self.base, self.index))


@dataclass(frozen=True)
class PartSelect(LogicTreeNode):
    """
    Represents a slice of bits: base[msb:lsb]
    Example: s[7:4]
    """

    base: LogicVar
    msb: int
    lsb: int
    width: int = field(init=False, default=1, repr=False)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "width", abs(self.msb - self.lsb) + 1)

    @property
    def depth(self) -> int:
        return self.base.depth if self.base else 0

    @property
    def delay(self):
        if hasattr(self.base, "delay"):
            return self.base.delay + 1  # selecting a range is usually a cheap op
        return 1

    def equals(self, other: "LogicTreeNode") -> bool:
        return (
            isinstance(other, PartSelect)
            and self.msb == other.msb
            and self.lsb == other.lsb
            and self.width == other.width
            and self.base.equals(other.base)
        )

    def __repr__(self) -> str:
        return f"{self.base}[{self.msb}:{self.lsb}]"

    def default_label(self) -> str:
        return str(self)

    def set_viz_label(self, label: str) -> None:
        object.__setattr__(self, "_viz_label", label)

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset({self.base})

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, PartSelect)
            and self.base == other.base
            and self.msb == other.msb
            and self.lsb == other.lsb
        )

    def __hash__(self) -> int:
        return hash((self.base, self.msb, self.lsb))


@dataclass(frozen=True)
class Concat(LogicTreeNode):
    """
    Represents a concatenation: { part1, part2, ... }
    Example: {a, b[3:0], 1'b0}
    """

    parts: List[LogicTreeNode]
    width: int = field(init=False, default=1, repr=False)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        total = 0
        for p in self.parts:
            if hasattr(p, "width"):
                total += p.width
            elif isinstance(p, int):
                total += 1
            else:
                raise TypeError(f"Concat operand has no width: {p}")
        object.__setattr__(self, "width", total)

    @property
    def depth(self) -> int:
        return 1 + max(part.depth for part in self.parts)

    @property
    def delay(self):
        delays = [p.delay for p in self.parts if hasattr(p, "delay")]
        return max(delays) if delays else 0

    def equals(self, other: "LogicTreeNode") -> bool:
        if not isinstance(other, Concat):
            return False
        if len(self.parts) != len(other.parts):
            return False
        return all(a.equals(b) for a, b in zip(self.parts, other.parts))

    def __repr__(self) -> str:
        return "{" + ", ".join(map(str, self.parts)) + "}"

    def default_label(self) -> str:
        return str(self)

    def set_viz_label(self, label: str) -> None:
        object.__setattr__(self, "_viz_label", label)

    def free_vars(self) -> FrozenSet[LogicVar]:
        fv = set()
        for p in self.parts:
            if hasattr(p, "free_vars"):
                fv |= p.free_vars()
            elif isinstance(p, LogicVar):
                fv.add(p)
        return frozenset(fv)

    def __eq__(self, other) -> bool:
        return isinstance(other, Concat) and tuple(self.parts) == tuple(other.parts)

    def __hash__(self) -> int:
        return hash(tuple(self.parts))
