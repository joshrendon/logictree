from dataclasses import dataclass
from logictree.nodes.ops.ops import LogicOp
from logictree.nodes.base.base import LogicTreeNode


@dataclass(frozen=True)
class ArithOp(LogicOp):
    """Base class for arithmetic operators."""
    left: LogicTreeNode
    right: LogicTreeNode


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
