from dataclasses import dataclass
from typing import List, Optional, Union

@dataclass
class IdNode:
    name: str

@dataclass
class Number:
    value: int

@dataclass
class BinaryOp:
    op: str
    left: object
    right: object

@dataclass
class UnaryOp:
    op: str
    operand: object

@dataclass
class Assign:
    target: str
    source: object

@dataclass
class Module:
    name: str
    ports: List[str]
    items: List[object]

@dataclass
class CaseItem:
    pattern: Union[IdNode, Number]
    statements: List[object]

@dataclass
class CaseStatement:
    expr: object
    items: List[CaseItem]
    default: Optional[List[object]] = None
