from logictree.nodes.base.base import LogicTreeNode


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
        # Treat as logic 0 or 'False'
        from sympy import false
        return false

    def to_verilog(self):
        return "1'b0"

    def free_vars(self):
        return set()

    def writes(self):
        return set()

