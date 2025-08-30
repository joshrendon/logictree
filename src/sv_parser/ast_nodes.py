from dataclasses import dataclass
from typing import List


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
