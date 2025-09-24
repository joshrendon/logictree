from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from functools import total_ordering
from typing import FrozenSet, Optional, Union

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.types import COMMUTATIVE_OPS

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LogicVar(LogicTreeNode):
    """Signal/variable reference in the IR."""

    name: str
    width: Optional[int] = None  # default = scalar
    is_signed: Optional[bool] = False
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def label(self) -> str:
        return self.name

    def __lt__(self, other):
        if not isinstance(other, LogicVar):
            return NotImplemented
        return self.name < other.name

    def __post_init__(self):
        LogicTreeNode.__init__(self)
        # Default width to 1 if not provided
        if self.width is None:
            object.__setattr__(self, "width", 1)

    def to_ir_dict(self):
        return {"type": "LogicVar", "name": self.name}

    def with_width(self, width: int) -> LogicVar:
        return LogicVar(self.name, width)

    def with_name(self, name: str):
        return replace(self, name=name)

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset({self})

    @property
    def op(self) -> str:
        return "VAR"

    @property
    def children(self):
        return []

    def equals(self, other):
        return isinstance(other, LogicVar) and self.name == other.name

    def __str__(self) -> str:
        return self.name

    def to_verilog(self):
        return self.name

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.name}", shape=ellipse];')
        if parent_id is not None:
            graph.append(f"  node{parent_id} -> node{my_id};")
        return my_id

    def __repr__(self):
        return f"LogicVar({self.name})"


@total_ordering
@dataclass(frozen=True)
class LogicConst(LogicTreeNode):
    """
    Verilog-faithful constant literal.

    - value: underlying numeric or boolean value. (bool coerces to int when needed)
    - width: optional bit width (e.g. 3 for 3'b101). If None, width is inferred on emission.
    - is_signed: signedness metadata for later codegen/semantics.
    - base: optional preferred base for emission: 'b' (binary), 'o' (octal), 'd' (decimal), 'h' (hex).
            If None, choose a sensible default based on original literal or width.
    - raw: optional raw literal text as parsed (e.g. "3'b101"). Kept for round-trip fidelity.
    """
    value: Union[int, bool, str]
    base: str = "d"
    width: Optional[int] = None
    is_signed: Optional[bool] = False
    raw: Optional[str] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        LogicTreeNode.__init__(self)

        # Parse Verilog-style string constants like "4'b1010"
        if isinstance(self.value, str):
            match = re.fullmatch(r"(\d+)'([bdho])([0-9a-fA-F_]+)", self.value)
            if match:
                width_str, base_str, digits = match.groups()
                #self.width = int(width_str)
                object.__setattr__(self, "width", int(width_str))
                base_map = {'b': 2, 'd': 10, 'h': 16, 'o': 8}
                base = base_map[base_str.lower()]
                clean_digits = digits.replace("_", "")
                self.value = int(clean_digits, base)
                self.base = base_str.lower()
            else:
                raise ValueError(f"Invalid Verilog-style constant string: {self.value}")

        # Validate int/bool types now
        if isinstance(self.value, bool):
            object.__setattr__(self, "width", 1)
        elif isinstance(self.value, int):
            # If width still None, infer from value
            if self.width is None:
                if self.value == 0:
                    object.__setattr__(self, "width", 1)
                else:
                    object.__setattr__(self, "width", self.value.bit_length())
        else:
            raise TypeError(f"Unsupported LogicConst value: {self.value} (type {type(self.value)})")

    @property
    def name(self) -> str:
        return self.label()

    def label(self) -> str:
        if self.width is None:
            return str(self.value)
        #bin_str = format(self.value, f"0{self.width}b") if self.width is not None else 1
        bin_str = format(self.value, f"0{self.width}b")
        return f"{self.width}'b{bin_str}"

    def __eq__(self, other):
        if isinstance(other, LogicConst):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, LogicConst):
            return self.value < other.value
        if isinstance(other, int):
            return self.value < other
        return NotImplemented

    def __hash__(self):
        return hash((self.value, self.width))

    def __add__(self, other):
        if isinstance(other, (LogicConst, int)):
            return self.value + (other.value if isinstance(other, LogicConst) else other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, (LogicConst, int)):
            return self.value - (other.value if isinstance(other, LogicConst) else other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, int):
            return other - self.value
        if isinstance(other, LogicConst):
            return other.value - self.value
        return NotImplemented

    def __int__(self):
        return self.value

    __repr__ = label # domain-style
    default_label = label

    def __str__(self) -> str:
        return self.to_verilog()

    def to_ir_dict(self):
        return {"type": "LogicConst", "value": self.value}

    def free_vars(self) -> FrozenSet[LogicVar]:
        return frozenset()

    @property
    def op(self):
        return "CONST"

    @property
    def children(self):
        return []

    def equals(self, other):
        return isinstance(other, LogicConst) and self.value == other.value

    @staticmethod
    def from_sv_literal(text: str) -> "LogicConst":
        """
        Parse SystemVerilog-style literals like:
        - 3'b101  (binary)
        - 12'hABC (hex)
        - '0, '1  (1-bit special)
        - 42      (plain decimal)
        - 8'd-3   (signed decimal with width)
        Returns a LogicConst preserving width/base/signedness.
        """
        s = text.strip().replace("_", "")
        # Width-prefixed?  N'<base><digits>
        # Examples: 3'b101, 12'habc, 8'd255, 4'o17
        import re

        m = re.fullmatch(r"(?i)(\d+)?'([sS]?)\s*([bodhBODH])\s*([0-9a-fxXzZ]+)", s)
        if m:
            width_str, sflag, base_char, digits = m.groups()
            width = int(width_str) if width_str else None
            is_signed = bool(sflag)
            base = base_char.lower()
            # Treat x/z as 0 numerically for now; you could extend to 4-value logic later.
            if any(ch in digits.lower() for ch in ("x", "z")):
                # Store raw for round-trip; numeric value as 0 for structural passes.
                return LogicConst(
                    value=0, width=width, is_signed=is_signed, base=base, raw=s
                )
            val = int(digits, {"b": 2, "o": 8, "d": 10, "h": 16}[base])
            return LogicConst(
                value=val, width=width, is_signed=is_signed, base=base, raw=s
            )

        # Special 1-bit `'0` or `'1`
        m2 = re.fullmatch(r"'\s*([01])", s)
        if m2:
            return LogicConst(
                value=int(m2.group(1)), width=1, is_signed=False, base="b", raw=s
            )

        # Plain decimal (possibly signed)
        try:
            val = int(s, 10)
            return LogicConst(
                value=val, width=None, is_signed=(val < 0), base="d", raw=s
            )
        except ValueError:
            # Fallback: store raw string literal as-is (e.g., parameters/macros you treat as consts)
            return LogicConst(value=s, width=None, is_signed=False, base=None, raw=s)

    @property
    def is_bool(self) -> bool:
        return isinstance(self.value, bool)

    def as_int(self) -> int:
        if isinstance(self.value, bool):
            return 1 if self.value else 0
        if isinstance(self.value, int):
            return self.value
        return 0

    def masked_int(self) -> int:
        v = self.as_int()
        if self.width is None:
            return v
        mask = (1 << self.width) - 1 if self.width > 0 else 0
        return v & mask

    def to_verilog(self) -> str:
        """
        Emit a Verilog-like literal preserving width/base when available.
        - If raw is present and you trust it, you can return raw directly.
        - Otherwise, format using width/base; default base is binary when width is known,
          else decimal.
        """
        if self.raw and "'" in self.raw:
            return self.raw
        val = self.masked_int()
        width = self.width
        base = (self.base or ("b" if width is not None else "d")).lower()
        sflag = "s" if self.is_signed else ""

        def digits(v: int, b: str) -> str:
            return {
                "b": bin(v)[2:] or "0",
                "o": oct(v)[2:] or "0",
                "d": str(v),
                "h": hex(v)[2:] or "0",
            }[b]

        if width is not None:
            return f"{width}'{sflag}{base}{digits(val, base)}"
        return (
            digits(val, base) if base == "d" else f"'{sflag}{base}{digits(val, base)}"
        )


    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.value}", shape=box];')
        if parent_id is not None:
            graph.append(f"  node{parent_id} -> node{my_id};")
        return my_id


@dataclass(frozen=True)
class LogicOp(LogicTreeNode, ABC):
    """Abstract base class for operator nodes (AND/OR/NOT/etc.)."""

    __slots__ = ("metadata",)

    def __init__(self, metadata=None):
        super().__init__()
        object.__setattr__(self, "metadata", metadata or {})

    @property
    def name(self):
        # AND, OR, NOT, XOR, XNOR, EQ, NEQ, MUX, etc.
        return self.__class__.__name__.replace("Op", "").upper()

    @property
    @abstractmethod
    def op(self) -> str:
        raise NotImplementedError(
            "Subclasses must implemnt the 'op' property"
        )  # subclasses: "AND"/"OR"/"XOR"/...

    @property
    @abstractmethod
    def operands(self) -> tuple["LogicTreeNode", ...]:
        raise NotImplementedError("Subclasses must implement the 'operands' property")

    def inputs(self):
        """Return child nodes in a list. Gate subclasses already expose a/b or operand."""
        # If subclasses already define inputs(), keep using that.
        # Otherwise, fall back to common attribute names.
        if hasattr(self, "_inputs"):
            return list(self._inputs)
        if hasattr(self, "a") and hasattr(self, "b"):
            return [self.a, self.b]
        if hasattr(self, "operand"):
            return [self.operand]
        return []

    # if this is still abstract, you can omit or provide a generic union
    def _children(self):
        # override in concrete ops if needed
        return self.children

    def free_vars(self) -> set[str]:
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = set().union(*(c.free_vars() for c in self._children()))
        try:
            # self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return s

    @property
    def children(self):
        return tuple(self.operands)

    def __str__(self):
        raise NotImplementedError("Subclasses must implement __str__()")

    def __repr__(self):
        return f"{self.__class__.__name__}(op={self.op!r}, operands={self.operands!r})"

    def pretty_inline(self):
        raise NotImplementedError("Subclasses must implement pretty_inline()")

    # def label(self):
    #    raise NotImplementedError("Subclasses must implement label()")

    def equals(self, other):
        if not isinstance(other, LogicOp):
            return False

        if self.op != other.op:
            return False
        if len(self.operands) != len(other.operands):
            return False

        # Commutative ops: Check operands ignoring order
        if self.op in COMMUTATIVE_OPS:
            self_sorted = sorted(self.operands, key=lambda x: str(x))
            other_sorted = sorted(self.operands, key=lambda x: str(x))
            return all(a.equals(b) for a, b in zip(self_sorted, other_sorted))

        # Non-commutative: preserve order
        return all(a.equals(b) for a, b in zip(self.operands, other.operands))

    def to_verilog(self):
        raise NotImplementedError("Subclasses must implement to_verilog()")

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError("Subclasses must implement to_dot()")

    def contains_hole(self):
        return any(inp.contains_hole() for inp in self.children)

    def simplify(self):
        raise RuntimeError(
            "LogicOp.simplify() removed. use logictree.transforms.simplify()"
        )


# Public API from this module
__all__ = ["LogicOp", "LogicConst", "LogicVar"]
