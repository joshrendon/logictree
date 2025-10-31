from abc import ABC
from dataclasses import dataclass

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicConst, LogicOp
from logictree.nodes.struct.structural import StructuralOp


@dataclass(frozen=True)
class ArithOp(LogicOp, StructuralOp, ABC):
    """Base class for arithmetic operators."""
    left: LogicTreeNode = LogicConst(0)
    right: LogicTreeNode = LogicConst(0)

    def __post_init__(self):
        pass

    def label(self):
        return self.__class__.__name__

    def to_json_dict(self):
        return {"type": self.__class__.__name__}

    def depth(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a structural node; "
            "depth undefined until lowered."
        )

    def delay(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a structural node; "
            "delay undefined until lowered."
        )



@dataclass(frozen=True)
class AddOp(ArithOp):
    def __post_init__(self):
        pass

    @property
    def op(self) -> str:
        return "+"

    @property
    def operands(self) -> tuple[LogicTreeNode, ...]:
        return (self.left, self.right)

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self):
        return f"{self.op}({repr(self.left)}, {repr(self.right)})"


@dataclass(frozen=True)
class SubOp(ArithOp):
    def __post_init__(self):
        pass

    @property
    def op(self) -> str:
        return "-"

    @property
    def operands(self) -> tuple[LogicTreeNode, ...]:
        return (self.left, self.right)

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self):
        return f"{self.op}({repr(self.left)}, {repr(self.right)})"

@dataclass(frozen=True)
class MulOp(ArithOp):
    def __post_init__(self):
        pass

    @property
    def op(self) -> str:
        return "*"

    @property
    def operands(self) -> tuple[LogicTreeNode, ...]:
        return (self.left, self.right)

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self):
        return f"{self.op}({repr(self.left)}, {repr(self.right)})"

@dataclass(frozen=True)
class DivOp(ArithOp):
    def __post_init__(self):
        pass

    @property
    def op(self) -> str:
        return "/"

    @property
    def operands(self) -> tuple[LogicTreeNode, ...]:
        return (self.left, self.right)

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self):
        return f"{self.op}({repr(self.left)}, {repr(self.right)})"
