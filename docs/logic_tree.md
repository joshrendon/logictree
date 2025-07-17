# LogicTree IR Overview

The LogicTree is a symbolic Boolean IR representing logic expressions.

Node types:
- `And(children)`, `Or(children)`, `Not(child)`
- `Id(name)`, `Const(value)`
- `Eq(left, right)`, `Xor(left, right)`

Used for visualization, depth analysis, and eventually synthesis.

