import logging
from dataclasses import field
from typing import FrozenSet, List, Optional

from logictree.nodes.ops.ops import LogicOp, LogicVar
from logictree.nodes.struct.statement import Statement

from ..base.base import LogicTreeNode

log = logging.getLogger(__name__)


def pretty_print_eq_label(op_node):
    if not isinstance(op_node, LogicOp) or op_node.op != "EQ":
        return "if(?)"
    if len(op_node.children) != 2:
        return "if(?)"
    lhs, rhs = op_node.children
    return f"{lhs.label()} == {rhs.label()}"


class IfStatement(Statement):
    metadata: dict = field(default_factory=dict, compare=False, repr=False)
    cond: LogicTreeNode
    then_branch: Statement
    else_branch: Optional[Statement] = None

    def __init__(self, cond, then_branch, else_branch=None):
        super().__init__()
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.children = []
        self._is_else_if = False  # for UI hinting, optional

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is None:
            acc = set(self.cond.free_vars())
            acc |= set(self.then_branch.free_vars())
            if self.else_branch:
                acc |= set(self.else_branch.free_vars())
            self._free_cache = frozenset(acc)
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        if self._w_cache is None:
            acc = set(self.then_branch.writes())
            if self.else_branch:
                acc |= set(self.else_branch.writes())
            self._w_cache = frozenset(acc)
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        if self._wm_cache is None:
            mt = self.then_branch.writes_must()
            me = self.else_branch.writes_must() if self.else_branch else frozenset()
            self._wm_cache = frozenset(mt & me) if self.else_branch else frozenset()
        return self._wm_cache

    def is_else_if(self) -> bool:
        return self._is_else_if

    def __repr__(self) -> str:
        return f"if({self.cond.label()})"

    def label(self) -> str:
        return f"if({self.cond.label()})"
    
    def pretty(self) -> str:
        return f"if {self.condition.pretty()}: {self.if_branch.pretty()} else: {self.else_branch.pretty()}"

    def default_label(self):
        cond_label = self.cond.label
        if cond_label == "EQ":
            log.warning(f" cond.label() = EQ; node = {repr(self.cond)}")
        return f"if({cond_label})"

    def get_children(self) -> List["LogicTreeNode"]:
        children = []
        if self.cond:
            children.append(self.cond)
        if self.then_branch:
            children.append(self.then_branch)
        if self.else_branch:
            if isinstance(self.else_branch, IfStatement):
                self.else_branch._is_else_if = True
            children.append(self.else_branch)
        return children
