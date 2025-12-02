import copy
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, FrozenSet, Iterator, List, Optional

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.struct.statement import BlockStatement, Statement

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from logictree.nodes.ops import LogicConst, LogicVar

from textwrap import indent as tw_indent


def _indent(text: str, spaces: int) -> str:
    return tw_indent(text, " " * spaces)

def iter_body(body) -> Iterator["Statement"]:
    """Iterate over the statements in a CaseItem/CaseStatement body safely."""
    if body is None:
        return iter(())
    if isinstance(body, BlockStatement):
        return iter(body.statements)
    if isinstance(body, list):
        return iter(body)
    raise TypeError(f"iter_body() Unexpected body type: {type(body)}")

def indent(text, spaces):
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())

@dataclass(frozen=True)
class CaseItem(LogicTreeNode):
    labels: List[LogicConst]
    body: BlockStatement
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
        if isinstance(self.body, list):
            raise TypeError("CaseItem.body must be a BlockStatement, not list")
        ## When the body is a plan Statement, force it to a List[Statement]
        #if isinstance(self.body, Statement):
        #    object.__setattr__(self, "body", [self.body])
        # if self.default:
        #    object.__setattr__(self, "labels", ["default"])
        # Validate default + labels
        #if self.default and not isinstance(self.default, EmptyBranch):
        #    if self.labels:
        if self.default and self.labels:
            object.__setattr__(self, "labels", ["default"])

    @property
    def statements(self):
        return self.body.statements

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
        #return f"CaseItem(labels={len(self.labels)}, body={type(self.body).__name__})"
        return f"CaseItem(num_labels={len(self.labels)}, labels={self.labels}, body={type(self.body).__name__})"

    def __str__(self):
        labels = ", ".join(str(l) for l in self.labels) if self.labels else "default"
        return (
            f"CASE_ITEM:\n"
            f"   label: {labels}\n"
            f"   body:\n"
            f"{indent(str(self.body), 6)}"
        )
    #def __str__(self):
    #    #label_str = ", ".join(str(l) for l in self.labels)
    #    #return f"CASE_ITEM:\n   labels: {label_str}\n   body:\n      {indent(str(self.body), 6)}"
    #    return f"CaseItem(num_labels={len(self.labels)}, labels={self.labels}, body={self.body})"

    def label(self) -> str:
        if self.default:
            return "default"
        return ", ".join(str(l) for l in self.labels)

    @property
    def children(self):
        kids: List[LogicTreeNode] = []
        # labels (constants or nodes)
        kids.extend(self.labels or [])
        # optional match expression
        if self.match is not None:
            kids.append(self.match)
        # body statements (flatten list)
        kids.extend(self.body or [])
        return kids

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
class CaseStatement(LogicTreeNode, Statement):
    selector: LogicTreeNode
    items: List[CaseItem] = field(default_factory=list)
    unique: bool = False
    default: Optional[List[Statement]] = None
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    from typing import List

    from logictree.nodes.ops.ops import LogicConst
    
    def __post_init__(self):
        from dataclasses import replace

        # Normalize None-> [] before touching it
        items = self.items if self.items is not None else []
        # Ensure items is a list (visitor sometimes gives tuple)
        items: List[CaseItem] = list(items)
    
        # Normalize 'default' passed via the default=... parameter
        dflt = self.default
        if isinstance(dflt, EmptyBranch):
            dflt = None
    
        # 1) First pass: extract/normalize a default arm from items if present
        default_item = dflt
        kept: List[CaseItem] = []
    
        def has_default_label(ci: CaseItem) -> bool:
            lbls = ci.labels or []
            return any(isinstance(x, str) and x.lower() == "default" for x in lbls)
    
        for it in items:
            if it.default or has_default_label(it):
                if default_item is not None:
                    raise ValueError("Multiple default arms in CaseStatement")
                # Canonicalize: default=True, labels=[]
                default_item = it if (it.default and not it.labels) else replace(it, default=True, labels=[])
                continue
            kept.append(it)
    
        # 2) Validate non-default labels AFTER normalization
        for it in kept:
            lbls = it.labels or []
            if not isinstance(lbls, list) or not all(isinstance(x, (int, LogicConst)) for x in lbls):
                raise TypeError(f"Bad labels on CaseItem: {lbls!r}")
    
        # 3) Commit normalized structure
        object.__setattr__(self, "items", kept)
        object.__setattr__(self, "default", default_item)

    def has_default(self) -> bool:
        return self.default is not None
    
    def default_is_empty(self) -> bool:
        return self.default is not None and len(self.default) == 0
    
    def default_is_noop(self) -> bool:
        """True if default has no effect: empty or only EmptyBranch nodes."""
        if self.default is None:
            return False
        if len(self.default) == 0:
            return True
        return all(isinstance(stmt, EmptyBranch) for stmt in self.default)

    def default_block(self) -> "BlockStatement":
        """Wrap default list into a BlockStatement for uniform handling."""
        if self.default is None:
            raise ValueError("No default present")
        return BlockStatement(self.default)
    #def __post_init__(self):
    #    from logictree.nodes.ops.ops import LogicConst

    #    for it in self.items:
    #        if it.default:
    #            continue  # Skip type check for default case (label = ["default"])
    #        if not isinstance(it.labels, list) or not all(
    #            isinstance(x, (int, LogicConst)) for x in it.labels
    #        ):
    #            raise TypeError(f"Bad labels on CaseItem: {it.labels!r}")

    def label(self) -> str:
        return f"case({self.selector})"

    def __repr__(self):
        n_items = len(self.items)
        has_def = self.has_default()
    
        # Guard: handle any parser inconsistency gracefully
        if self.default is None:
            def_len = 0
        elif isinstance(self.default, list):
            def_len = len(self.default)
        elif hasattr(self.default, "body"):  # CaseItem-like
            try:
                def_len = len(getattr(self.default, "body", []))
            except Exception:
                def_len = 1
        else:
            def_len = 1
    
        return (
            f"CaseStatement(selector={self.selector}, unique={self.unique}, "
            f"items={n_items}, has_default={has_def}, default_len={def_len})"
        )
    #def __repr__(self):
    #    n_items = len(self.items)
    #    has_def = self.has_default()
    #    def_len = 0 if self.default is None else len(self.default)
    #    return (f"CaseStatement(selector={self.selector}, unique={self.unique}, "
    #            f"items={n_items}, has_default={has_def}, default_len={def_len})")
    #def __repr__(self):
    #    return f"CaseStatement(selector={self.selector}, default={self.default}, items={self.items})"

    def free_vars(self) -> FrozenSet[LogicVar]:
        """Return all LogicVar instances read inside this case statement."""
        if self._free_cache is not None:
            return self._free_cache
    
        vars = set()
        vars.update(self.selector.free_vars())
    
        # Traverse each CaseItem
        for item in self.items:
            if item.body:
                for stmt in item.body:        # BlockStatement is iterable now
                    vars.update(stmt.free_vars())
    
        # Traverse default branch if present
        if self.default and getattr(self.default, "body", None):
            for stmt in self.default.body:
                vars.update(stmt.free_vars())
    
        object.__setattr__(self, "_free_cache", frozenset(vars))
        return self._free_cache

    def writes(self) -> FrozenSet[LogicVar]:
        if self._w_cache is not None:
            return self._w_cache

        vars = set()
        for item in self.items:
            log.debug(f"item: {item}")
            if item.body:
                for stmt in item.body:
                    vars.update(stmt.writes())
        # Include writes from default branch, if any
        if self.default and getattr(self.default, "body", None):
            for stmt in self.default.body:
                vars.update(stmt.writes())

        object.__setattr__(self, "_w_cache", frozenset(vars))
        return self._w_cache

    def writes_must(self) -> FrozenSet[LogicVar]:
        if self._wm_cache is not None:
            return self._wm_cache
    
        # --- Gather writes from each explicit case arm ---
        branch_writes: list[set[LogicVar]] = []
        for item in self.items:
            w = set()
            if item.body:
                for stmt in item.body:
                    w.update(stmt.writes())
            branch_writes.append(w)
    
        # --- Normalize default: treat EmptyBranch as None ---
        dflt = self.default
        if isinstance(dflt, EmptyBranch):
            dflt = None
    
        # --- No default → conservative empty must-writes ---
        if dflt is None:
            must = set()
        else:
            default_writes: set[LogicVar] = set()
            if dflt.body:
                for stmt in dflt.body:
                    default_writes.update(stmt.writes())
    
            # Variables written in every branch OR written in the default
            # *and* in at least one branch qualify as must-writes.
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
    #def writes_must(self) -> FrozenSet[LogicVar]:
    #    """
    #    A variable is a must-write if the arm that executes (for any selector value)
    #    always assigns to it.
    #
    #    Conservative rules:
    #      - No default: we assume selector values may exist that match no item → ∅.
    #      - With default: variable must be written in every case item AND in default.
    #    """
    #    if self._wm_cache is not None:
    #        return self._wm_cache
    #
    #    # Collect per-item write sets
    #    branch_writes: list[set[LogicVar]] = []
    #    for item in self.items:
    #        w: set[LogicVar] = set()
    #        if item.body:
    #            for stmt in item.body:           # BlockStatement is iterable
    #                w.update(stmt.writes())
    #        branch_writes.append(w)
    #
    #    if self.default is None:
    #        # Without a default, we can’t guarantee total coverage of selector space.
    #        must: set[LogicVar] = set()
    #    else:
    #        # Default is normalized to a CaseItem with a BlockStatement body
    #        default_writes: set[LogicVar] = set()
    #        if self.default.body:
    #            for stmt in self.default.body:
    #                default_writes.update(stmt.writes())
    #
    #        if not branch_writes:
    #            # Degenerate case: only default present
    #            must = default_writes
    #        else:
    #            # Must be written in every case item AND in default
    #            must = set.intersection(*branch_writes) & default_writes
    #
    #    object.__setattr__(self, "_wm_cache", frozenset(must))
    #    return self._wm_cache
    #def writes_must(self) -> FrozenSet[LogicVar]:
    #    """
    #    Compute the set of variables that are *must-writes* for this case statement.

    #    Semantics:
    #      - A variable is considered a "must-write" if every possible execution path
    #        through the case assigns to it.

    #      - With no `default` arm, only variables written in *all* case items qualify
    #        (pure intersection of branch writes).

    #      - With a `default` arm, coverage is extended: if the default writes a
    #        variable, then for any selector value not handled by an explicit case,
    #        that variable is guaranteed to be assigned. In that situation:
    #          * If a variable is written in every case arm → it's a must-write.
    #          * If a variable is written in the default AND in at least one case arm,
    #            it's also a must-write, since together those cover the entire selector space.

    #    Examples:
    #      case (s)
    #        0: y = a;
    #        1: y = b;
    #        // no default
    #      endcase
    #        → writes_must = {}  (y not guaranteed, selector may be != 0/1)

    #      case (s)
    #        0: y = a;
    #        1: z = b;
    #        default: y = c;
    #      endcase
    #        → writes_must = {y}  (y is always assigned: either by case0 or default;
    #                              z is conditional, only in one branch)

    #      case (s)
    #        0: y = a;
    #        1: y = b;
    #        default: y = c;
    #      endcase
    #        → writes_must = {y}  (y written in all arms including default)
    #    """
    #    if self._wm_cache is not None:
    #        return self._wm_cache

    #    if not self.items:
    #        object.__setattr__(self, "_wm_cache", frozenset())
    #        return self._wm_cache

    #    branch_writes = []
    #    for it in self.items:
    #        w = set()
    #        for stmt in iter_body(it.body):
    #            w.update(stmt.writes())
    #        branch_writes.append(w)

    #    if self.default is None:
    #        object.__setattr__(self, "_wm_cache", frozenset())
    #        return self._wm_cache

    #    default_writes = set()
    #    for stmt in iter_body(self.default.body if self.default else None):
    #        default_writes.update(stmt.writes())

    #    must = set()
    #    all_written = set().union(*branch_writes, default_writes)
    #    for v in all_written:
    #        in_all_cases = all(v in bw for bw in branch_writes)
    #        in_default_and_some = (v in default_writes) and any(
    #            v in bw for bw in branch_writes
    #        )
    #        if in_all_cases or in_default_and_some:
    #            must.add(v)

    #    object.__setattr__(self, "_wm_cache", frozenset(must))
    #    return self._wm_cache

    @property
    def children(self):
        kids: List[LogicTreeNode] = []
        # selector expression
        if self.selector is not None:
            kids.append(self.selector)
        # case items
        kids.extend(self.items or [])
        # optional default body statements
        if self.default:
            kids.extend(self.default)
        return kids

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

    #def __str__(self):
    #    case_items_str = "\n".join(indent(str(item), 2) for item in self.items)
    #    return f"CASE(\n  {str(self.selector)}\n{case_items_str}\n)"

    
    def __str__(self):
        lines = []
        lines.append("CASE(")
        lines.append(f"  {self.selector}")
    
        # Items
        for it in self.items:
            lines.append(_indent(str(it), 2))
    
        # Default
        if self.default is not None:
            lines.append("  DEFAULT:")
            if len(self.default) == 0:
                lines.append("    /* empty */")
            else:
                body = BlockStatement(self.default)
                lines.append(_indent(str(body), 4))
    
        lines.append(")")
        return "\n".join(lines)
    #def __str__(self):
    #    s = f"CASE(\n  {self.selector}\n"
    #    for item in self.items:
    #        s += f"  {item}\n"
    #    if self.default is not None:
    #        s += "  DEFAULT:\n"
    #        # Here, pass an int for indentation
    #        s += f"{indent(str(self.default), 4)}\n"
    #    s += ")"
    #    return s

    def default_label(self):
        return f"case({self.selector})"

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
                    "labels": [str(lbl) for lbl in item.labels],
                    "default": item.default,
                    "body": [
                        stmt.to_ir_dict() if hasattr(stmt, "to_ir_dict") else str(stmt)
                        for stmt in item.body
                    ],
                }
                for item in self.items
            ],
        }

    def clone(self):
        return CaseStatement(
            selector=(
                self.selector.clone()
                if hasattr(self.selector, "clone")
                else copy.deepcopy(self.selector)
            ),
            items=[item.clone() for item in self.items],
        )
