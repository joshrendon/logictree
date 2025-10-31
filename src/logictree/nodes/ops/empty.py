from dataclasses import dataclass

from logictree.nodes.base.base import LogicTreeNode


@dataclass(frozen=True)
class EmptyBranch(LogicTreeNode):
    """Singleton node representing an empty else/default branch."""

    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmptyBranch, cls).__new__(cls)
        return cls._instance

    @property
    def operands(self):
        return ()

    @property
    def children(self):
        return ()

    def label(self) -> str:
        return "<empty>"

    def __repr__(self):
        return "EmptyBranch"

    def __str__(self):
        return "(empty)"

    def to_sympy_expr(self):
        raise NotImplementedError("Need to implement to_sympy_expr")

    def to_verilog(self):
        raise NotImplementedError("Need to implement to_verilog")

    def free_vars(self):
        return set()

    def writes(self):
        return set()

