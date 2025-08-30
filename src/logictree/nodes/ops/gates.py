from dataclasses import field

from ..base.base import LogicTreeNode
from .ops import LogicOp

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


class NotOp(LogicOp):
    metadata: dict = field(default_factory=dict, compare=False, repr=False)
    operand: LogicTreeNode

    def __init__(self, operand):
        super().__init__()
        self._set_inputs([operand])
        self.operand = operand
        self.child = operand

    def _children(self):
        return (self.operand,)

    @property
    def op(self):
        return "NOT"

    def label(self):
        return self.op

    def default_label(self):
        return "NOT"

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

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class AndOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        # already primitive
        return AndOp(self.lhs, self.rhs)

    def equals(self, other):
        return _commutative_equals(self, other)

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "op": self.op,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class OrOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        # already primitive
        return OrOp(self.lhs, self.rhs)

    def equals(self, other):
        return _commutative_equals(self, other)

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class XorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        # (a & ~b) | (~a & b)
        na = NotOp(self.lhs)
        nb = NotOp(self.rhs)
        return OrOp(AndOp(self.lhs, nb), AndOp(na, self.rhs))

    def equals(self, other):
        return _commutative_equals(self, other)

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class XnorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        # ~(a ^ b)
        return NotOp(XorOp(self.lhs, self.rhs))

    def equals(self, other):
        return _commutative_equals(self, other)

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class NandOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        return NotOp(AndOp(self.lhs, self.rhs))

    def equals(self, other):
        return _commutative_equals(self, other)

    # def to_json_dict(self):
    #    return {
    #        "type": self.__class__.__name__,
    #        "label": self.label(),
    #        "depth": self.depth,
    #        "delay": self.delay,
    #        "expr_source": self.expr_source,
    #        "children": [ch.to_json_dict() for ch in self.children],
    #    }


class NorOp(LogicOp):
    a: LogicTreeNode
    b: LogicTreeNode
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __init__(self, a, b):
        super().__init__()
        self._set_inputs([a, b])
        self.a = a
        self.b = b

    def _children(self):
        return (self.a, self.b)

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

    def to_primitives(self):
        return NotOp(OrOp(self.lhs, self.rhs))

    def equals(self, other):
        return _commutative_equals(self, other)


__all__ = ["AndOp", "OrOp", "NotOp", "XorOp", "XnorOp", "NandOp", "NorOp"]
