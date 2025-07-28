from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List
from dataclasses import dataclass
from logictree.utils.display import indent

@dataclass
class CaseItem(LogicTreeNode):
    def __init__(self, *, labels: list[LogicTreeNode], body: LogicTreeNode):
        self.labels = labels
        self.body   = body

    def __repr__(self):
        return f"CaseItem(labels={len(self.labels)}, body={type(self.body).__name__})"

    def __str__(self):
        #return f"CaseItem({self.labels}, {self.body})"
        label_str = ", ".join(str(l) for l in self.labels)
        return f"CASE_ITEM:\n   labels: {label_str}\n   body:\n      {indent(str(self.body), 6)}"

    def inputs(self):
        inputs = set()
        inputs.update(self.labels.inputs())
        for item in self.labels:
            inputs.update(item.body.inputs())
        return list(inputs)

    match: Optional[LogicTreeNode]  # None if default
    body: LogicTreeNode
    default: bool = False
    #default: LogicConst(0)

@dataclass
class CaseStatement(LogicTreeNode):
    selector: LogicTreeNode
    items: List[CaseItem]
    def inputs(self):
        inputs = set()
        inputs.update(self.selector.inputs())
        for item in self.items:
            inputs.update(item.body.inputs())
        return list(inputs)
    def __str__(self):
        #return f"CASE({self.selector}, {self.items})"
        case_items_str = "\n".join(indent(str(item), 2) for item in self.items)
        return f"CASE(\n  {str(self.selector)}\n{case_items_str}\n)"
