from ..base.base import LogicTreeNode
from typing import List, Union

class NotOp(LogicOp):
    def __init__(self, child):
        super().__init__('NOT', [child])
    
