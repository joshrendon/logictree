from logictree.nodes import (
    AndOp,
    BitSelect,
    CaseStatement,
    Concat,
    EqOp,
    IfStatement,
    LogicAssign,
    LogicConst,
    LogicVar,
    Module,
    NeqOp,
    NotOp,
    OrOp,
    PartSelect,
    XorOp,
)


def evaluate(n, env):
    # High-level / structural nodes
    if isinstance(n, Module):
        # raise TypeError("evaluate() should not be called on Module; pass one of its output expressions instead.")
        return
    if isinstance(n, LogicAssign):
        return evaluate(n.rhs, env)
    if isinstance(n, IfStatement):
        cond_val = evaluate(n.cond, env)
        branch = n.then_branch if cond_val else n.else_branch
        return evaluate(branch, env)
    if isinstance(n, CaseStatement):
        for it in n.items:
            labels = getattr(it, "labels", None)
            if labels in (None, [], "default"):
                continue
            # tolerate accidental ints to avoid type errors during bring-up
            if isinstance(labels, int):
                labels = [labels]
            if evaluate(n.selector, env) in labels:
                return evaluate(it.body, env)

        # default arm
        for it in n.items:
            if getattr(it, "labels", None) == "default":
                return evaluate(it.body, env)
        return 0  # no matching arm

    # Leaves
    if isinstance(n, LogicConst):
        return int(n.value) & ((1 << n.width) - 1)

    if isinstance(n, LogicVar):
        return int(env[n.name]) & 1

    if isinstance(n, BitSelect):
        base_name = n.base.name
        return int(env[f"{base_name}[{n.index}]"]) & 1

    if isinstance(n, PartSelect):
        base_name = n.base.name
        bits = []
        rng = range(n.lsb, n.msb + 1) if n.lsb <= n.msb else range(n.lsb, n.msb - 1, -1)
        for i in rng:
            bits.append(int(env[f"{base_name}[{i}]"]) & 1)
        # msb is highest index; fold down into an int
        return sum(b << idx for idx, b in enumerate(bits))

    if isinstance(n, Concat):
        val = 0
        for p in n.parts:  # MSB-first
            part_val = evaluate(p, env)
            part_width = getattr(p, "width", 1)
            val = (val << part_width) | (part_val & ((1 << part_width) - 1))
        return val

    # Eq Op
    if isinstance(n, EqOp):
        lhs_val = evaluate(n.lhs, env)
        rhs_val = evaluate(n.rhs, env)
        return int(lhs_val == rhs_val)

    # Neq
    if isinstance(n, NeqOp):
        lhs_val = evaluate(n.lhs, env)
        rhs_val = evaluate(n.rhs, env)
        return int(lhs_val != rhs_val)

    # Gates
    if isinstance(n, NotOp):
        return 1 ^ evaluate(n.operand, env)
    if isinstance(n, AndOp):
        return evaluate(n.a, env) & evaluate(n.b, env)
    if isinstance(n, OrOp):
        return evaluate(n.a, env) | evaluate(n.b, env)
    if isinstance(n, XorOp):
        return evaluate(n.a, env) ^ evaluate(n.b, env)

    # If we get here, we truly don't support this node
    raise TypeError(f"Unsupported node for evaluate(): {type(n).__name__}")
