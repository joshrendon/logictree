from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List
from dataclasses import dataclass
from logictree.utils.formating import indent
from logictree.transforms import case_to_if_tree
import logging
import copy
log = logging.getLogger(__name__)

@dataclass
class CaseItem(LogicTreeNode):
    def __init__(self, labels, body):
        super().__init__()
        self.labels = labels
        self.body = body
        self.children = labels + ([body] if body else [])

    labels: list[LogicTreeNode]
    body: LogicTreeNode
    match: Optional[LogicTreeNode] = None  # Some IRs may use this
    default: bool = False

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
        return CaseItem(
            labels=self.labels,
            body=self.body.simplify() if hasattr(self.body, "simplify") else self.body
        )

    def clone(self):
        return CaseItem(
            labels=[copy.deepcopy(label) for label in self.labels],
            body=self.body.clone() if hasattr(self.body, "clone") else copy.deepcopy(self.body)
        )


@dataclass
class CaseStatement(LogicTreeNode):
    def __init__(self, selector, items: List[CaseItem]):
        super().__init__()
        self.selector = selector
        self.items = items  # List of CaseItem instances
    selector: LogicTreeNode
    items: List[CaseItem]

    def children(self):
        return [self.selector] + [item.body for item in self.items]

    def flatten(self):
        return case_to_if_tree(self).simplify()

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

    def simplify(self):
        try:
            from logictree.transforms import case_to_if_tree
            lowered = case_to_if_tree(self)
            return lowered
        except Exception as e:
            log.warning(f"[simplify:CaseStatement] Lowering failed: {e}")
            return self

    def clone(self):
        return CaseStatement(
            selector=self.selector.clone() if hasattr(self.selector, "clone") else copy.deepcopy(self.selector),
            items=[item.clone() for item in self.items]
        )


