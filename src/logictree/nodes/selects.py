from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import FrozenSet, List

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops import LogicConst, LogicVar

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BitSelect(LogicTreeNode):
    """
    Represents a single-bit selection: base[index]
    Example: s[3]
    """
    base: LogicTreeNode | str
    index: LogicTreeNode | int
    width: int = field(init=False, default=1, repr=False)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "base",  self._normalize(self.base))
        object.__setattr__(self, "index", self._normalize(self.index))
        object.__setattr__(self, "width", 1)

    def label(self):
        if isinstance(self.index, LogicConst):
            return f"{self.base.label()}[{int(self.index.value)}]"
        return f"{self.base.label()}[{self.index}]"

    __repr__ = label  # repr same as label

    default_label = label

    @property
    def children(self):
        return [self.base, self.index]

    @property
    def operands(self):
        return [self.base, self.index]

    def equals(self, other: "LogicTreeNode") -> bool:
        return (
            isinstance(other, BitSelect)
            and self.index == other.index
            and self.base.equals(other.base)
        )


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

    base: LogicTreeNode | str
    msb: LogicTreeNode | int
    lsb: LogicTreeNode | int
    width: int = field(init=False, default=1, repr=False)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def _normalize_self(self) -> "PartSelect":
        """Ensure msb and lsb are always in descending order."""
        # Normalize children first using base class static method
        base = LogicTreeNode._normalize(self.base)
        msb = LogicTreeNode._normalize(self.msb)
        lsb = LogicTreeNode._normalize(self.lsb)
        log.debug("_normalize_self()")

        # Ensure msb and lsb are LogicConst nodes
        assert isinstance(msb, LogicConst), f"msb is not LogicConst: {msb!r}"
        assert isinstance(lsb, LogicConst), f"lsb is not LogicConst: {lsb!r}"

        # Only normalize if both msb and lsb are constants
        if isinstance(msb, LogicConst) and isinstance(lsb, LogicConst):
            if msb.value < lsb.value:
                msb, lsb = lsb, msb

        return PartSelect(base=base, msb=msb, lsb=lsb)

    def __post_init__(self):
        base = LogicTreeNode._normalize(self.base)
        msb = LogicTreeNode._normalize(self.msb)
        lsb = LogicTreeNode._normalize(self.lsb)
        log.debug("__post_init__")
    
        def describe(name, val):
            return f"{name}: {val!r} (type={type(val)})"
    
        log.debug("[PartSelect DEBUG]")
        log.debug(describe("base", base))
        log.debug(describe("msb", msb))
        log.debug(describe("lsb", lsb))
    
        try:
            msb_val = msb.value if isinstance(msb, LogicConst) else msb
            lsb_val = lsb.value if isinstance(lsb, LogicConst) else lsb
            log.debug(f"msb_val: {msb_val!r} (type={type(msb_val)})")
            log.debug(f"lsb_val: {lsb_val!r} (type={type(lsb_val)})")
    
            width = abs(msb_val - lsb_val) + 1
            log.debug(f"width: {width}")
        except TypeError:
            log.error("[ERROR in PartSelect width calc] symbolic bounds, defering width = Unknown")
            width = None
        except Exception as e:
            log.error(f"[ERROR in PartSelect width calc] {e.__class__.__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
        object.__setattr__(self, "base", base)
        object.__setattr__(self, "msb", msb)
        object.__setattr__(self, "lsb", lsb)
        object.__setattr__(self, "width", width)

    def equals(self, other: "LogicTreeNode") -> bool:
        return (
            isinstance(other, PartSelect)
            and self.msb == other.msb
            and self.lsb == other.lsb
            and self.width == other.width
            and self.base.equals(other.base)
        )

    def set_viz_label(self, label: str) -> None:
        object.__setattr__(self, "_viz_label", label)

    def free_vars(self) -> FrozenSet[LogicVar]:
        #return frozenset({self.base})
        return {v for v in self.base.free_vars()}

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, PartSelect)
            and self.base == other.base
            and self.msb == other.msb
            and self.lsb == other.lsb
        )

    def __hash__(self) -> int:
        return hash((self.base, self.msb, self.lsb))

    def label(self) -> str:
        if isinstance(self.msb, LogicConst) and isinstance(self.lsb, LogicConst):
            return f"{self.base.label()}[{int(self.msb.value)}:{int(self.lsb.value)}]"
        #return f"{self.base.label()}[{self.msb.label()}:{self.lsb.label()}]"
        return f"{self.base.label()}[{self.msb}:{self.lsb}]"

    __repr__ = label
    default_label = label


    @property
    def children(self):
        return [self.base, self.msb, self.lsb]

    @property
    def operands(self):
        return [self.base, self.msb, self.lsb]


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
        if not isinstance(self.parts, (list, tuple)):
            object.__setattr__(self, "parts", [self.parts])
        for p in self.parts:
            if hasattr(p, "width"):
                total += p.width
            elif isinstance(p, int):
                total += 1
            else:
                raise TypeError(f"Concat operand has no width: {p}")
        object.__setattr__(self, "width", total)
        object.__setattr__(self, "parts", [self._normalize(p) for p in self.parts])

    def label(self) -> str:
        return "{" + ", ".join([p.label() for p in self.parts]) + "}"

    __repr__ = label
    default_label = label

    @property
    def children(self):
        return [self.parts]

    @property
    def operands(self):
        return tuple(self.parts)

    def equals(self, other: "LogicTreeNode") -> bool:
        if not isinstance(other, Concat):
            return False
        if len(self.parts) != len(other.parts):
            return False
        return all(a.equals(b) for a, b in zip(self.parts, other.parts))

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
