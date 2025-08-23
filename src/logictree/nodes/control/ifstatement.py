import logging
from dataclasses import field
from typing import FrozenSet, List, Optional

from logictree.nodes.ops.ops import LogicVar
from logictree.nodes.struct.statement import Statement

from ..base.base import LogicTreeNode

log = logging.getLogger(__name__)

def pretty_print_eq_label(op_node):
    from logictree.nodes.ops.ops import LogicOp
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
        self._viz_label = None
        self._is_else_if = False  # for UI hinting, optional

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is None:
            acc = set(self.cond.free_vars())
            acc |= set(self.then_block.free_vars())
            if self.else_block:
                acc |= set(self.else_block.free_vars())
            self._free_cache = frozenset(acc)
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        if self._w_cache is None:
            acc = set(self.then_block.writes())
            if self.else_block:
                acc |= set(self.else_block.writes())
            self._w_cache = frozenset(acc)
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        if self._wm_cache is None:
            mt = self.then_block.writes_must()
            me = self.else_block.writes_must() if self.else_block else frozenset()
            self._wm_cache = frozenset(mt & me) if self.else_block else frozenset()
        return self._wm_cache

    def is_else_if(self) -> bool:
        return self._is_else_if

    def label(self):
        if self._viz_label:
            return self._viz_label
        return self.default_label()
    
    def default_label(self):
        cond_label = self.cond.label()
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

    @property
    def depth(self) -> int:
        branches = [self.then_branch]
        if self.else_branch:
            branches.append(self.else_branch)
        return 1 + max([self.cond.depth] + [b.depth for b in branches])

    @property
    def delay(self) -> int:
        def safe_delay(node):
            return getattr(node, "delay", 0) or 0
        branches = [self.then_branch]
        if self.else_branch:
            branches.append(self.else_branch)
        return 1 + max([safe_delay(self.cond)] + [safe_delay(b) for b in branches])

    def to_json_dict(self):
        children = self.get_children()
        if not children:
            log.warning(f" IfStatement id={id(self)} has no children!")
    
        log.debug(f" IfStatement to_json_dict() - children count: {len(children)}")
        for idx, child in enumerate(children):
            log.debug(f"  child[{idx}] type: {type(child).__name__} label: {child.label()}")
    
        log.debug(f" IfStatement.to_json_dict label={self.label} label()={self.label()} _viz_label={self._viz_label}")
        
        return {
            "type": "IfStatement",
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            "expr_source": None,
            "children": [child.to_json_dict() for child in children],
        }

class FlattenedIfStatement(LogicTreeNode):
    metadata: dict = field(default_factory=dict, compare=False, repr=False)
    def __init__(self, cond, then_branch, else_if_branches=None, else_branch=None):
        super().__init__()
        self.cond= cond
        self.then_branch = then_branch
        self.else_if_branches  = []
        self.else_branch = else_branch

        self.children = []
        if self.cond:
            self.children.append(self.cond)
        if self.then_branch:
            self.children.append(self.then_branch)
        if self.else_branch:
            self.children.append(self.else_branch)

        current = self
        while isinstance(current.else_branch, IfStatement):
            self.else_if_branches.append((current.else_branch.cond, current.else_branch.then_branch))
            current = current.else_branch
        self.else_branch = current.else_branch

    def default_label(self):
        return "FlattenedIfStatement"

    @property
    def depth(self):
        # Conservative depth: max depth across all branches
        all_branches = [self.then_branch] + [b for _, b in self.else_if_branches]
        if self.else_branch:
            all_branches.append(self.else_branch)
        return 1 + max((b.depth for b in all_branches), default=0)

    @property
    def delay(self):
        return 0 #TODO: Return a real value not just 0

    def is_else_if(self):
        return getattr(self, "_is_else_if", False)

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay
        }
    
