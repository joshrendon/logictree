import copy
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, FrozenSet, Iterator, List, Optional

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.struct.statement import Statement
from logictree.utils.formating import indent

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from logictree.nodes.ops import LogicConst, LogicVar


def iter_body(body: list[Statement] | None) -> Iterator[Statement]:
    """Iterate over the statements in a CaseItem/CaseStatement body safely."""
    if body is None:
        return iter(())
    return iter(body)


@dataclass(frozen=True)
class CaseItem(LogicTreeNode):
    labels: List[LogicConst]
    body: List[Statement]
    default: bool = False
    match: Optional[LogicTreeNode] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    _free_cache: Optional[FrozenSet[LogicVar]] = field(
        default=None, init=False, repr=False, compare=False
    )
    _writes_cache: Optional[FrozenSet[LogicVar]] = field(
        default=None, init=False, repr=False, compare=False
    )
    _writes_must_cache: Optional[FrozenSet[LogicVar]] = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self):
        LogicTreeNode.__init__(self)
        # When the body is a plan Statement, force it to a List[Statement]
        if isinstance(self.body, Statement):
            object.__setattr__(self, "body", [self.body])
        # if self.default:
        #    object.__setattr__(self, "labels", ["default"])
        # Validate default + labels
        if self.default:
            if self.labels:
                raise ValueError(
                    f"Default CaseItem cannot have user-defined labels: labels={self.labels}"
                )
            object.__setattr__(
                self, "labels", ["default"]
            )  # safe to set here after check

    @property
    def is_default(self) -> bool:
        return self.default or any(l == "default" for l in self.labels)

    def free_vars(self) -> FrozenSet[LogicVar]:
        """Free vars come from labels (if not default) + match expression."""
        vars = set()

        if not self.default:
            for label in self.labels:
                vars.update(label.free_vars())

        vars.update(self.match.free_vars())
        return frozenset(vars)

    def writes(self) -> FrozenSet[LogicVar]:
        """CaseItem never writes anything directly."""
        return frozenset()

    def writes_must(self) -> FrozenSet[LogicVar]:
        return frozenset()

    def __repr__(self):
        log.debug("CaseItem __repr__ called with labels: %s", self.labels)
        return f"CaseItem(labels={len(self.labels)}, body={type(self.body).__name__})"

    def __str__(self):
        label_str = ", ".join(str(l) for l in self.labels)
        return f"CASE_ITEM:\n   labels: {label_str}\n   body:\n      {indent(str(self.body), 6)}"

    def label(self) -> str:
        if self.default:
            return "default"
        return ", ".join(l.label() for l in self.labels)

    def to_json_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "children": [self.body.to_json_dict()],
            "delay": getattr(self.body, "delay", 0),
            "depth": getattr(self.body, "depth", 0),
            "expr_source": None,
        }

    def inputs(self):
        inputs = set()
        if self.match:
            inputs.update(self.match.inputs())
        if self.body:
            inputs.update(self.body.inputs())
        return list(inputs)

    def simplify(self):
        import warnings

        warnings.warn(
            ".simplify() is deprecated; use simplify_logic_tree(node) instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @property
    def depth(self) -> int:
        return self.body.depth if self.body else 0

    @property
    def delay(self):
        return self.body.delay if hasattr(self.body, "delay") else 0

    def clone(self):
        return CaseItem(
            labels=copy.deepcopy(self.labels),
            match=copy.deepcopy(self.match),
            body=(
                self.body.clone()
                if hasattr(self.body, "clone")
                else copy.deepcopy(self.body)
            ),
            default=self.default,
            metadata=copy.deepcopy(self.metadata),
        )


@dataclass(frozen=True)
class CaseStatement(Statement):
    selector: LogicTreeNode
    items: List[CaseItem]
    default: Optional[List[Statement]] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        from logictree.nodes.ops.ops import LogicConst

        for it in self.items:
            if it.default:
                continue  # Skip type check for default case (label = ["default"])
            if not isinstance(it.labels, list) or not all(
                isinstance(x, (int, LogicConst)) for x in it.labels
            ):
                raise TypeError(f"Bad labels on CaseItem: {it.labels!r}")

    def label(self) -> str:
        return f"case({self.selector})"

    def __repr__(self):
        return f"CaseStatement(selector={self.selector}, items={len(self.items)})"

    def free_vars(self) -> FrozenSet[LogicVar]:
        if self._free_cache is not None:
            return self._free_cache

        vars = set()
        vars.update(self.selector.free_vars())

        for it in self.items:
            for stmt in iter_body(it.body):
                vars.update(stmt.free_vars())

        if self.default:
            for stmt in iter_body(self.default):
                vars.update(stmt.free_vars())

        object.__setattr__(self, "_free_cache", frozenset(vars))
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        if self._w_cache is not None:
            return self._w_cache

        vars = set()
        for it in self.items:
            for stmt in iter_body(it.body):
                vars.update(stmt.writes())
        if self.default:
            for stmt in iter_body(self.default):
                vars.update(stmt.writes())

        object.__setattr__(self, "_w_cache", frozenset(vars))
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        """
        Compute the set of variables that are *must-writes* for this case statement.

        Semantics:
          - A variable is considered a "must-write" if every possible execution path
            through the case assigns to it.

          - With no `default` arm, only variables written in *all* case items qualify
            (pure intersection of branch writes).

          - With a `default` arm, coverage is extended: if the default writes a
            variable, then for any selector value not handled by an explicit case,
            that variable is guaranteed to be assigned. In that situation:
              * If a variable is written in every case arm → it's a must-write.
              * If a variable is written in the default AND in at least one case arm,
                it's also a must-write, since together those cover the entire selector space.

        Examples:
          case (s)
            0: y = a;
            1: y = b;
            // no default
          endcase
            → writes_must = {}  (y not guaranteed, selector may be != 0/1)

          case (s)
            0: y = a;
            1: z = b;
            default: y = c;
          endcase
            → writes_must = {y}  (y is always assigned: either by case0 or default;
                                  z is conditional, only in one branch)

          case (s)
            0: y = a;
            1: y = b;
            default: y = c;
          endcase
            → writes_must = {y}  (y written in all arms including default)
        """
        if self._wm_cache is not None:
            return self._wm_cache

        if not self.items:
            object.__setattr__(self, "_wm_cache", frozenset())
            return self._wm_cache

        branch_writes = []
        for it in self.items:
            w = set()
            for stmt in iter_body(it.body):
                w.update(stmt.writes())
            branch_writes.append(w)

        if self.default is None:
            object.__setattr__(self, "_wm_cache", frozenset())
            return self._wm_cache

        default_writes = set()
        for stmt in iter_body(self.default):
            default_writes.update(stmt.writes())

        must = set()
        all_written = set().union(*branch_writes, default_writes)
        for v in all_written:
            in_all_cases = all(v in bw for bw in branch_writes)
            in_default_and_some = (v in default_writes) and any(
                v in bw for bw in branch_writes
            )
            if in_all_cases or in_default_and_some:
                must.add(v)

        object.__setattr__(self, "_wm_cache", frozenset(must))
        return self._wm_cache

    def children(self):
        return [self.selector] + [item.body for item in self.items]

    def simplify(self):
        """Node-local simplification only. Use transforms.case_to_if.case_to_if_tree for structural rewrites."""
        import warnings

        warnings.warn(
            ".simplify() is deprecated; use simplify_logic_tree(node) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self  # keep local invariants only; no cross-module transforms here

    def flatten(self):
        """Use transforms functions instead (this is now a no-op)."""
        return self

    def inputs(self):
        inputs = set()
        inputs.update(self.selector.inputs())
        for item in self.items:
            inputs.update(item.body.inputs())
        return list(inputs)

    def __str__(self):
        case_items_str = "\n".join(indent(str(item), 2) for item in self.items)
        return f"CASE(\n  {str(self.selector)}\n{case_items_str}\n)"

    def default_label(self):
        return f"case({self.selector})"

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "selector": self.selector.to_json_dict(),
            "children": [item.to_json_dict() for item in self.items],
            "depth": self.depth,
            "delay": self.delay,
        }

    def to_ir_dict(self):
        return {
            "type": "CaseStatement",
            "label": self.label(),
            "selector": (
                self.selector.to_ir_dict()
                if hasattr(self.selector, "to_ir_dict")
                else self.selector.label()
            ),
            "items": [
                {
                    "labels": [lbl.label() for lbl in item.labels],
                    "default": item.default,
                    "body": [
                        stmt.to_ir_dict() if hasattr(stmt, "to_ir_dict") else str(stmt)
                        for stmt in item.body
                    ],
                }
                for item in self.items
            ],
        }

    @property
    def depth(self) -> int:
        item_depths = [item.body.depth or 0 for item in self.items if item.body]
        return 1 + max([self.selector.depth or 0] + item_depths)

    @property
    def delay(self) -> int:
        item_delays = [item.body.delay or 0 for item in self.items if item.body]
        return 1 + max([self.selector.delay or 0] + item_delays)

    def clone(self):
        return CaseStatement(
            selector=(
                self.selector.clone()
                if hasattr(self.selector, "clone")
                else copy.deepcopy(self.selector)
            ),
            items=[item.clone() for item in self.items],
        )
