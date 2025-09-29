from enum import Enum
from dataclasses import dataclass

class DataType(Enum):
    LOGIC = "logic"
    REG   = "reg"
    WIRE  = "wire"

@dataclass(frozen=True)
class LogicType:
    kind: DataType      # "logic", "reg", "wire"
    width: int = 1
