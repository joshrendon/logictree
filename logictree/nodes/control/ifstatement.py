from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List

class IfStatement(LogicTreeNode):
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition        # Expression node
        self.then_body = then_body        # Could be assignment or block
        self.else_body = else_body        # Optional: either another IfStatement or block
