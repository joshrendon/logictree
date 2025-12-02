from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    LOGIC = "logic"
    REG   = "reg"
    WIRE  = "wire"

@dataclass(frozen=True)
class LogicType:
    kind: DataType      # "logic", "reg", "wire"
    width: int = 1
