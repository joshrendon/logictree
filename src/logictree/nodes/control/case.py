from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.struct.statement import Statement
from typing import Dict, Tuple, Union, Optional, List, TYPE_CHECKING, FrozenSet, Set
from dataclasses import dataclass, field 
from logictree.utils.formating import indent

import logging
import copy
log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from logictree.nodes.ops import LogicConst, LogicVar, LogicOp

@dataclass(frozen=True)
class CaseItem(LogicTreeNode):
    labels: Tuple[LogicConst, ...]
    body: Statement
    default: bool = False
    match: Optional[LogicTreeNode] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    _free_cache: Optional[FrozenSet[LogicVar]] = field(default=None, init=False, repr=False, compare=False)
    _writes_cache: Optional[FrozenSet[LogicVar]] = field(default=None, init=False, repr=False, compare=False)
    _writes_must_cache: Optional[FrozenSet[LogicVar]] = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.default:
            assert len(self.labels) == 1 and self.labels[0].value == "default"
        if self.default or (self.labels and self.labels[0].value == "default"):
            return "case default"
        if self.default and self.labels:
            raise ValueError("Default CaseItem cannot have labels")
    @property
    def is_default(self) -> bool:
        return (
            len(self.labels) == 1
            and isinstance(self.labels[0], LogicConst)
            and self.labels[0].value == "default"
        )

    def free_vars(self) -> FrozenSet[LogicVar]:
        """Free vars come from labels (if not default) + match expression."""
        vars = set()

        if not self.default:
            for label in self.labels:
                vars.update(label.free_vars())

        vars.update(self.match.free_vars())
        return frozenset(vars)

    def writes(self) -> FrozenSet[LogicVar]:
        """CaseItem never writes anything directly."""
        return frozenset()

    def writes_must(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def __repr__(self):
        log.debug("CaseItem __repr__ called with labels: %s", self.labels)
        return f"CaseItem(labels={len(self.labels)}, body={type(self.body).__name__})"

    def __str__(self):
        label_str = ", ".join(str(l) for l in self.labels)
        return f"CASE_ITEM:\n   labels: {label_str}\n   body:\n      {indent(str(self.body), 6)}"

    def label(self) -> str:
        if self.default:
            return "case default"
        label_strs = [str(lbl) for lbl in self.labels]
        return f"case {', '.join(label_strs)}"

    def to_json_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "children": [self.body.to_json_dict()],
            "delay": getattr(self.body, "delay", 0),
            "depth": getattr(self.body, "depth", 0),
            "expr_source": None,
        }

    def inputs(self):
        inputs = set()
        if self.match:
            inputs.update(self.match.inputs())
        if self.body:
            inputs.update(self.body.inputs())
        return list(inputs)

    def simplify(self):    
        import warnings
        from logictree.transforms.simplify import simplify_logic_tree
        warnings.warn(
            ".simplify() is deprecated; use simplify_logic_tree(node) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        body = simplify_logic_tree(self.body)
        return CaseItem(
            labels=self.labels,
            match=self.match,
            body=body,
            default=self.default,
            metadata=copy.deepcopy(self.metadata)
        )

    def clone(self):
        return CaseItem(
            labels=copy.deepcopy(self.labels),
            match=copy.deepcopy(self.match),
            body=self.body.clone() if hasattr(self.body, "clone") else copy.deepcopy(self.body),
            default=self.default,
            metadata=copy.deepcopy(self.metadata)
        )

@dataclass(frozen=True)
class CaseStatement(Statement):
    selector: LogicTreeNode
    items: List[CaseItem]
    default: Optional[Statement] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        from logictree.nodes.ops.ops import LogicConst
        for it in self.items:
            if it.labels != "default":
                if not isinstance(it.labels, list) or not all(isinstance(x, (int, LogicConst)) for x in it.labels):
                    raise TypeError(f"Bad labels on CaseItem: {it.labels!r}")

    def label(self) -> str:
        return f"case({self.selector})"

    def __repr__(self):
        return f"CaseStatement(selector={self.selector}, items={len(self.items)})"

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is not None:
            return self._free_cache

        vars = set()
        vars.update(self.selector.free_vars())

        for it in self.items:
            vars.update(it.body.free_vars())

        if self.default:
            vars.update(self.default.body.free_vars())

        object.__setattr__(self, "_free_cache", frozenset(vars))
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        if self._w_cache is not None:
            return self._w_cache

        vars = set()
        for item in self.items:
            vars.update(item.body.writes())
        if self.default is not None:
            vars.update(self.default.body.writes())
        object.__setattr__(self, "_w_cache", frozenset(vars))
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        if self._wm_cache is not None:
            return self._wm_cache

        if not self.items:
            object.__setattr__(self, "_wm_cache", frozenset())
            return self._wm_cache

        must_writes = self.items[0].body.writes()
        for item in self.items[1:]:
            must_writes &= item.body.writes()

        if self.default is not None:
            must_writes &= self.default.body.writes()

        object.__setattr__(self, "_wm_cache", frozenset(must_writes))
        return self._wm_cache

    def children(self):
        return [self.selector] + [item.body for item in self.items]

    def simplify(self):
        """Node-local simplification only. Use transforms.case_to_if.case_to_if_tree for structural rewrites."""
        import warnings
        #from logictree.transforms.simplify import simplify_logic_tree
        warnings.warn(
            ".simplify() is deprecated; use simplify_logic_tree(node) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self  # keep local invariants only; no cross-module transforms here

    def flatten(self):
        """Use transforms functions instead (this is now a no-op)."""
        return self

    def inputs(self):
        inputs = set()
        inputs.update(self.selector.inputs())
        for item in self.items:
            inputs.update(item.body.inputs())
        return list(inputs)

    def __str__(self):
        case_items_str = "\n".join(indent(str(item), 2) for item in self.items)
        return f"CASE(\n  {str(self.selector)}\n{case_items_str}\n)"

    def default_label(self):
        return f"case({self.selector})"

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "selector": self.selector.to_json_dict(),
            "children": [item.to_json_dict() for item in self.items],
            "depth": self.depth,
            "delay": self.delay,
        }

    def to_ir_dict(self):
        return {
            "type": "CaseStatement",
            "label": self.label(),
            "selector": self.selector.to_ir_dict() if hasattr(self.selector, "to_ir_dict") else self.selector.label(),
            "items": [
                {
                    "labels": [lbl.label() for lbl in item.labels],
                    "default": item.default,
                    "body": [
                        stmt.to_ir_dict() if hasattr(stmt, "to_ir_dict") else str(stmt)
                        for stmt in item.body
                    ]
                }
                for item in self.items
            ]
        }

    @property
    def depth(self) -> int:
        item_depths = [item.body.depth or 0 for item in self.items if item.body]
        return 1 + max([self.selector.depth or 0] + item_depths)
    
    @property
    def delay(self) -> int:
        item_delays = [item.body.delay or 0 for item in self.items if item.body]
        return 1 + max([self.selector.delay or 0] + item_delays)

    def clone(self):
        return CaseStatement(
            selector=self.selector.clone() if hasattr(self.selector, "clone") else copy.deepcopy(self.selector),
            items=[item.clone() for item in self.items]
        )

