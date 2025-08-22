from collections import Counter

PRIMS = {"AND","OR","NOT"}
COMPOUND = {"XOR","XNOR","NAND","NOR"}

def gate_count(root, *, primitives_only: bool = True) -> Counter:
    node = root.to_primitives() if primitives_only and hasattr(root, "to_primitives") else root
    seen, counts = set(), Counter()
    def visit(n):
        nid = id(n)
        if nid in seen: return
        seen.add(nid)
        op = getattr(n, "op", None)
        if op in PRIMS or (not primitives_only and op in PRIMS|COMPOUND):
            counts[op] += 1
        for ch in getattr(n, "children", ()):
            visit(ch)
    visit(node)
    return counts

def total_gates(root, **kw) -> int:
    return sum(gate_count(root, **kw).values())

