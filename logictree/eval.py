from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.ops.gates import AndOp, OrOp, XorOp, NotOp
from logictree.nodes.struct.module import Module

def _is_default_item(it: CaseItem) -> bool:
    # Be liberal: treat “default” if it has no labels, None, or explicit flag
    return (
        getattr(it, "is_default", False)
        or getattr(it, "labels", None) in (None, [], "default")
    )


def evaluate(n, env):
    print(f"DEBUG: n: {n}")
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
        sel_val = evaluate(n.selector, env)

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
        #for it in n.items:
        #    labels = getattr(it, "labels", None)
        #    if labels not in (None, [], "default") and sel_val in labels:
        #        return evaluate(it.body, env)
        #for it in n.items:
        #    if _is_default_item(it):
        #        return evaluate(it.body, env)
        return 0  # no matching arm

    # Leaves
    if isinstance(n, LogicConst):
        return int(n.value) & 1
    if isinstance(n, LogicVar):
        return int(env[n.name]) & 1

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
#def evaluate(n, env):
#    # Control nodes first
#    if isinstance(n, LogicAssign):
#        return evaluate(n.rhs, env)
#
#    if isinstance(n, IfStatement):
#        cond_val = evaluate(n.cond, env)
#        branch = n.then_branch if cond_val else n.else_branch
#        return evaluate(branch, env)
#
#    if isinstance(n, CaseStatement):
#        sel_val = evaluate(n.selector, env)
#        # try labeled items
#        for it in n.items:
#            labels = getattr(it, "labels", None)
#            if labels not in (None, [], "default") and sel_val in labels:
#                return evaluate(it.body, env)
#        # default
#        for it in n.items:
#            if _is_default_item(it):
#                return evaluate(it.body, env)
#        # no match, fall back to 0
#        return 0
#
#    # Existing gate-based evaluation
#    print(f"DEBUG: n: {n}")
#    op = getattr(n, "op", None)
#    if op == "CONST": return int(n.value) & 1
#    if op == "VAR":   return int(env[n.name]) & 1
#    if op == "NOT":   return 1 ^ evaluate(n.children[0], env)
#    if op == "AND":   return evaluate(n.children[0], env) & evaluate(n.children[1], env)
#    if op == "OR":    return evaluate(n.children[0], env) | evaluate(n.children[1], env)
#    if op == "XOR":   return evaluate(n.children[0], env) ^ evaluate(n.children[1], env)
#    #if op is None: return 0
#
#    print(f"DEBUG: Not Implemented op: {op}")
#    raise NotImplementedError(op)

