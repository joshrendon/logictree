from dataclasses import dataclass
from enum import Enum
from typing import Optional

from logictree.nodes.struct.statement import BlockStatement, Statement


class AlwaysKind(Enum):
    COMB = "comb"
    SEQ  = "seq"

@dataclass(frozen=True)
class AlwaysBlock(Statement):
    """Represents an always @* or always @(posedge clk) block."""

    kind: AlwaysKind
    label: Optional[str] = None   # from begin : label
    body: BlockStatement = BlockStatement()

    def free_vars(self):
        return self.body.free_vars()

    def writes(self):
        return self.body.writes()

    def writes_must(self):
        return self.body.writes_must()
