from collections import Counter
import logging

log = logging.getLogger(__name__)

PRIMS = {"AND", "OR", "NOT"}
COMPOUND = {"XOR", "XNOR", "NAND", "NOR"}

CONTROL_NODES = {
    "CaseStatement",
    "CaseItem",
    "IfStatement",
    "LogicAssign",
}

def gate_count(root, *, primitives_only: bool = True) -> Counter:
    node = (
        root.to_primitives()
        if primitives_only and hasattr(root, "to_primitives")
        else root
    )
    seen, counts = set(), Counter()

    def visit(n):
        nid = id(n)
        if nid in seen:
            return
        seen.add(nid)

        op = getattr(n, "op", None)
        if op in PRIMS or (not primitives_only and op in PRIMS | COMPOUND):
            counts[op] += 1
        elif op is None and type(n).__name__ in CONTROL_NODES:
            log.warning(
                f"gate_count() called on control-level node {type(n).__name__} "
                f"before lowering. Counts may be incomplete."
            )

        # always recurse through children
        kids = getattr(n, "children", [])
        if callable(kids):
            log.warning(f"{type(n).__name__}.children is a method, not property")
            kids = kids()
        for ch in kids:
            visit(ch)

    visit(node)
    return counts

def total_gates(root, **kw) -> int:
    return sum(gate_count(root, **kw).values())
