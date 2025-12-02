from dataclasses import dataclass, field

from ..base.base import LogicTreeNode
from .ops import LogicOp, LogicVar

__all__ = ["NotOp", "AndOp", "OrOp", "XorOp", "XnorOp", "NandOp", "NorOp"]


def _commutative_equals(a, b):
    # assumes children = [lhs, rhs]
    return a.__class__ is b.__class__ and (
        (a.children[0].equals(b.children[0]) and a.children[1].equals(b.children[1]))
        or (a.children[0].equals(b.children[1]) and a.children[1].equals(b.children[0]))
    )


def _flatten_same(op_cls, ops):
    flat = []
    for o in ops:
        if isinstance(o, op_cls):
            flat.extend(o.operands)
        else:
            flat.append(o)
    return flat


@dataclass(frozen=True)
class NotOp(LogicOp):
    operand: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        assert not isinstance(self.operand, list), "NotOp operand should be a single LogicTreeNode"
        object.__setattr__(self, "operand", LogicTreeNode._normalize(self.operand))
        object.__setattr__(self, "width", 1)

    @property
    def op(self):
        return "NOT"

    def label(self):
        if isinstance(self.operand, LogicVar):
            return f"{self.operand.name} == 1'b0"
        return f"~({self.operand.label() if hasattr(self.operand, 'label') else self.operand})"

    #def label(self):
    #    return self.op

    def default_label(self):
        return "NOT"

    @property
    def child(self):
        return self.operand

    @property
    def children(self):
        return [self.operand]

    @property
    def operands(self):
        return [self.operand]

    def __str__(self):
        return f"(~{self.operand})"

    def __repr__(self):
        return f"NotOp({repr(self.operand)})"

    def equals(self, other):
        return isinstance(other, NotOp) and self.operand.equals(other.operand)


@dataclass(frozen=True)
class AndOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", self._normalize(self.a))
        object.__setattr__(self, "b", self._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "AND"

    def label(self):
        return self.op

    def default_label(self):
        return "AND"

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    def __str__(self):
        return f"({self.a} & {self.b})"

    def __repr__(self):
        return f"AndOp({repr(self.a)}, {repr(self.b)})"

    def equals(self, other):
        return _commutative_equals(self, other)


@dataclass(frozen=True)
class OrOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", self._normalize(self.a))
        object.__setattr__(self, "b", self._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "OR"

    def label(self):
        return self.op

    def default_label(self):
        return "OR"

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    def __str__(self):
        return f"({self.a} | {self.b})"

    def __repr__(self):
        return f"OrOp({repr(self.a)}, {repr(self.b)})"

    def equals(self, other):
        return _commutative_equals(self, other)


@dataclass(frozen=True)
class XorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", LogicTreeNode._normalize(self.a))
        object.__setattr__(self, "b", LogicTreeNode._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "XOR"

    def label(self):
        return self.op

    def __str__(self):
        return f"({self.a} ^ {self.b})"

    def default_label(self):
        return "XOR"

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    def equals(self, other):
        return _commutative_equals(self, other)


@dataclass(frozen=True)
class XnorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", self._normalize(self.a))
        object.__setattr__(self, "b", self._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "XNOR"

    def label(self):
        return self.op

    def default_label(self):
        return "XNOR"

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    def __str__(self):
        return f"~({self.a} ^ {self.b})"

    def equals(self, other):
        return _commutative_equals(self, other)


@dataclass(frozen=True)
class NandOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", self._normalize(self.a))
        object.__setattr__(self, "b", self._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "NAND"

    def label(self):
        return self.op

    def default_label(self):
        return "NAND"

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    def __str__(self):
        return f"~({self.a} & {self.b})"

    def equals(self, other):
        return _commutative_equals(self, other)


@dataclass(frozen=True)
class NorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "a", self._normalize(self.a))
        object.__setattr__(self, "b", self._normalize(self.b))
        object.__setattr__(self, "width", 1)

    @property
    def op(self) -> str:
        return "NOR"

    def label(self):
        return self.op

    def default_label(self):
        return "NOR"

    def __str__(self):
        return f"~({self.a} | {self.b})"

    @property
    def left(self):
        return self.operands[0]

    @property
    def right(self):
        return self.operands[1]

    @property
    def children(self):
        return [self.a, self.b]

    @property
    def operands(self):
        return [self.a, self.b]

    def equals(self, other):
        return _commutative_equals(self, other)

__all__ = ["AndOp", "OrOp", "NotOp", "XorOp", "XnorOp", "NandOp", "NorOp"]
