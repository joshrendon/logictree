#from ..base.base import LogicTreeNode
from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from typing import Dict, Tuple, Union, Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field
from logictree.utils.formating import indent

import logging
import copy
log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from logictree.nodes.ops import LogicConst, LogicVar, LogicOp

@dataclass(frozen=True)
class CaseItem(LogicTreeNode):
    #labels: list[int] | list[LogicTreeNode]
    labels: Union[str, List[int]]
    body: LogicTreeNode
    match: Optional[LogicTreeNode] = None  # Some IRs may use this
    default: bool = False
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        if self.labels != "default":
            if not isinstance(self.labels, list) or not all(isinstance(x, int) for x in self.labels):
                raise TypeError(f"CaseItem.labels must be 'default' or List[int], got {self.labels!r}")

    def free_vars(self) -> set[str]:
        # labels are constants in your current tests, so ignore
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = self.body.free_vars()
        try:
            #self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return set(s)

    def __repr__(self):
        log.debug("CaseItem __repr__ called with labels: %s", self.labels)
        return f"CaseItem(labels={len(self.labels)}, body={type(self.body).__name__})"

    def __str__(self):
        label_str = ", ".join(str(l) for l in self.labels)
        return f"CASE_ITEM:\n   labels: {label_str}\n   body:\n      {indent(str(self.body), 6)}"

    def label(self) -> str:
        if self.labels:
            return f"case {', '.join([l.label() for l in self.labels])}"
        return "case default"

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
        for label in self.labels:
            inputs.update(label.inputs())
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
        #return simplify_logic_tree(self)
        return CaseItem(
            labels=self.labels,
            body=body
        )

    def clone(self):
        return CaseItem(
            labels=[copy.deepcopy(label) for label in self.labels],
            body=self.body.clone() if hasattr(self.body, "clone") else copy.deepcopy(self.body)
        )


@dataclass(frozen=True)
class CaseStatement(LogicTreeNode):
    #def __init__(self, selector, items: List[CaseItem]):
    #    super().__init__()
    #    self.selector = selector
    #    self.items = items  # List of CaseItem instances
    selector: LogicTreeNode
    items: List[CaseItem] = field(default_factory=list)
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        for it in self.items:
            if it.labels != "default":
                if not isinstance(it.labels, list) or not all(isinstance(x, int) for x in it.labels):
                    raise TypeError(f"Bad labels on CaseItem: {it.labels!r}")

    def free_vars(self) -> set[str]:
        if hasattr(self, "_free_vars"):
            return set(self._free_vars)
        s = set(self.selector.free_vars())
        for it in self.items:
            s |= it.free_vars()
        try:
            #self._free_vars = set(s)
            object.__setattr__(self, "_free_vars", set(s))  # ok with frozen dataclasses
        except Exception:
            pass  # caching is optional; correctness doesn’t depend on it
        return set(s)

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


