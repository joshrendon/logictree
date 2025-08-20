from logictree.nodes.base import LogicTreeNode
from typing import List, Union, Optional, Tuple
from logictree.utils.display import indent
from logictree.utils import overlay
from logictree.nodes.types import GATE_TYPES, COMMUTATIVE_OPS
from dataclasses import dataclass, replace, field
from abc import abstractmethod
import logging
log = logging.getLogger(__name__)

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
    width: Optional[int] = None
    is_signed: bool = False
    base: Optional[str] = None
    raw: Optional[str] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        LogicTreeNode.__init__(self)

    def __str__(self) -> str:
        return self.to_verilog()

    def label(self) -> str:
        viz = overlay.get_viz_label(self)
        return viz if viz is not None else str(self.value)

    def free_vars(self) -> set[str]:
        return set()

    @property
    def delay(self):
        return 0

    @property
    def op(self):
        return "CONST"

    @property
    def children(self): #leaf
        return []

    @property
    def children(self):
        return  []
    
    def equals(self, other):
        return isinstance(other, LogicConst) and self.value == other.value

    #def inputs(self) -> set[str]:
    #    return self.collect_input_names()

    @property
    def depth(self):
        return 0

    # ---- Construction helpers ---------------------------------------------
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
                return LogicConst(value=0, width=width, is_signed=is_signed, base=base, raw=s)
            val = int(digits, {"b":2, "o":8, "d":10, "h":16}[base])
            return LogicConst(value=val, width=width, is_signed=is_signed, base=base, raw=s)

        # Special 1-bit `'0` or `'1`
        m2 = re.fullmatch(r"'\s*([01])", s)
        if m2:
            return LogicConst(value=int(m2.group(1)), width=1, is_signed=False, base="b", raw=s)

        # Plain decimal (possibly signed)
        try:
            val = int(s, 10)
            return LogicConst(value=val, width=None, is_signed=(val < 0), base="d", raw=s)
        except ValueError:
            # Fallback: store raw string literal as-is (e.g., parameters/macros you treat as consts)
            return LogicConst(value=s, width=None, is_signed=False, base=None, raw=s)

    # ---- Int/bit operations -----------------------------------------------
    @property
    def is_bool(self) -> bool:
        return isinstance(self.value, bool)
    def as_int(self) -> int:
        if isinstance(self.value, bool): return 1 if self.value else 0
        if isinstance(self.value, int):  return self.value
        return 0

    def masked_int(self) -> int:
        v = self.as_int()
        if self.width is None: return v
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
            return {"b": bin(v)[2:] or "0", "o": oct(v)[2:] or "0", "d": str(v), "h": hex(v)[2:] or "0"}[b]
        if width is not None:
            return f"{width}'{sflag}{base}{digits(val, base)}"
        return digits(val, base) if base == "d" else f"'{sflag}{base}{digits(val, base)}"

    def equals(self, other: object) -> bool:
        if not isinstance(other, LogicConst):
            return False
        # Consider constants equal if their masked numeric values and widths/sign match when specified.
        same_num = self.masked_int() == other.masked_int()
        same_w = (self.width == other.width) or (self.width is None or other.width is None)
        same_s = (self.is_signed == other.is_signed) or (self.is_signed is False and other.is_signed is False)
        return same_num and same_w and same_s

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "value": self.value,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            #"expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }


    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.value}", shape=box];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def __repr__(self):
        return f"LogicConst({self.value})"

    #def collect_input_names(self) -> set[str]:
    #    return set()


@dataclass(frozen=True)
class LogicVar(LogicTreeNode):
    """Signal/variable reference in the IR."""
    name: str
    width: Optional[int] = None
    is_signed: bool = False
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        LogicTreeNode.__init__(self)

    def with_width(self, width: int, *, is_signed: Optional[bool] = None) -> "LogicVar":
        return replace(self, width=width, is_signed=self.is_signed if is_signed is None else is_signed)

    def with_name(self, name: str) -> "LogicVar":
        return replace(self, name=name)

    def free_vars(self) -> set[str]:
        # cache optional
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = {self.name}

        try:
            #self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return s

    def label(self) -> str:
        viz = overlay.get_viz_label(self)
        return viz if viz is not None else self.name

    @property
    def delay(self):
        return 0

    @property
    def op(self) -> str:
        return "VAR"

    @property
    def children(self): #leaf
        return []

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            #"expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }
        
    @property
    def children(self):
        return  []

    def equals(self, other):
        return isinstance(other, LogicVar) and self.name == other.name

    def __str__(self) -> str:
        return self.name

    # TODO: remove mokeypatched __repr__
    def __repr__(self):
        return f"LogicVar(name={self.name})"

    #def inputs(self) -> set[str]:
    #    return self.collect_input_names()

    @property
    def depth(self):
        return 0

    def to_verilog(self):
        return self.name

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.name}", shape=ellipse];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def __repr__(self):
        return f"LogicVar({self.name})"

    #def collect_input_names(self) -> set[str]:
    #    return {self.name}


class LogicOp(LogicTreeNode):
    """Base for operator nodes (AND/OR/NOT/etc.)."""
    name: str = "OP"
    def __init__(self, *inputs):
        super().__init__()
        if type(self) is LogicOp:
            raise TypeError("LogicOp is an abstract base class and cannot be instantiated")
        self._inputs:  list[LogicTreeNode] = []

    def _set_inputs(self, seq):
        self._inputs = list(seq)

    @property
    def name(self):
        # AND, OR, NOT, XOR, XNOR, EQ, NEQ, MUX, etc.
        return self.__class__.__name__.replace('Op', '').upper()

    @property
    @abstractmethod
    def op(self):
        raise NotImplementedError("Subclasses must implemnt the 'op' property")  # subclasses: "AND"/"OR"/"XOR"/...

    @property
    @abstractmethod
    def operands(self):
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
        return getattr(self, "children", ())

    def free_vars(self) -> set[str]:
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = set().union(*(c.free_vars() for c in self._children()))
        try:
            #self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return s

    def to_json_dict(self) -> dict:
        return {
            "type": type(self).__name__,
            "children": [c.to_json_dict() for c in self.inputs()],
        }

    @property
    #def children(self) -> list["LogicTreeNode"]:
    def children(self):
        return tuple(self.operands)

    @property 
    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(op.depth for op in self.children)

    @property
    def delay(self) -> int:
        # Naively: 1 unit per level
        return self.depth

    def __str__(self):
        raise NotImplementedError("Subclasses must implement __str__()")

    def __repr__(self):
        return f"{self.__class__.__name__}(op={self.op!r}, operands={self.operands!r})"
    
    def pretty_inline(self):
        raise NotImplementedError("Subclasses must implement pretty_inline()")

    def label(self):
        raise NotImplementedError("Subclasses must implement label()")

    #def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [child.to_json_dict() for child in self.children],
    #    }

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
        from logictree.transforms.simplify import simplify_logic_tree
        return simplify_logic_tree(self)

# Public API from this module
__all__ = ["LogicOp", "LogicConst", "LogicVar"]
