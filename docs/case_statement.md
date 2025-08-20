### Documentation on CaseStatement / CaseItem Class-Interface Expectations

#### CaseItem:
```

@dataclass(frozen=True)
class CaseItem:
    match: LogicTreeNode
    labels: List[LogicTreeNode]
    body: Statement
    default: bool = False
```
  * match: Used internally to identify the arm — not used in execution.
  * labels: A list of LogicConst or LogicTreeNode used to match against the selector.
  * body: Must be a Statement node (e.g., LogicAssign, IfStatement, etc.)
  * default: Set to True only on the default arm. Optional; CaseStatement should still work without one.
#### CaseStatement:

```

@dataclass(frozen=True)
class CaseStatement(Statement):
    selector: LogicTreeNode
    items: Tuple[CaseItem, ...]
    default: Optional[CaseItem] = None
```
  * selector: Typically a LogicVar to match against each arm's label.
  * items: Tuple of CaseItem, each containing labels and bodies.
  * default: Optional fallback case, expected to be marked default=True.

### Key Behavior:
* All interfaces (free_vars(), writes(), writes_must()) now return FrozenSet[LogicVar], ensuring proper type propagation through nested statements.

### Role of Statement and LogicTreeNode
`LogicTreeNode (Base Class)`
* Foundation for all nodes in the logic tree.
* Supports introspection, tree manipulation, and core semantic APIs like:
  * `free_vars()`
  * `simplify()`
  * `to_json_dict()`
`Statement` (New Base Class for Logic Statements)
* Inherits from `LogicTreeNode`, allows specialization for control-flow and dataflow nodes (like `LogicAssign`, `IfStatement`, `CaseStatement`)
* Allows uniform analysis for:
  * Read/write tracking
  * Simplification or transformation pipelines
