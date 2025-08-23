from functools import singledispatch

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp


@singledispatch
def simplify(node):
    return node

@simplify.register(NotOp)
def _(node: NotOp) -> LogicTreeNode:
    operand = simplify(node.operand)
    if isinstance(operand, NotOp):
        return operand.operand
    if isinstance(operand, LogicConst):
        return LogicConst(1 - operand.value)
    return NotOp(operand)

@simplify.register
def _(node: AndOp):
    a = simplify(node.a)
    b = simplify(node.b)

    # domination / identity
    if (isinstance(a, LogicConst) and a.value == 0) or (isinstance(b, LogicConst) and b.value == 0):
        return LogicConst(0)
    if isinstance(a, LogicConst) and a.value == 1:
        return b
    if isinstance(b, LogicConst) and b.value == 1:
        return a

    # idempotence: a & a -> a
    if a.equals(b):
        return a

    return AndOp(a, b)

@simplify.register
def _(node: OrOp):
    a = simplify(node.a)
    b = simplify(node.b)

    # domination / identity
    if (isinstance(a, LogicConst) and a.value == 1) or (isinstance(b, LogicConst) and b.value == 1):
        return LogicConst(1)
    if isinstance(a, LogicConst) and a.value == 0:
        return b
    if isinstance(b, LogicConst) and b.value == 0:
        return a

    # idempotence: a | a -> a
    if a.equals(b):
        return a

    return OrOp(a, b)

@simplify.register(XorOp)
def _(node: XorOp) -> LogicTreeNode:
    a = simplify(node.a)
    b = simplify(node.b)
    # ... (unchanged logic, but use simplify not simplify_logic_tree)
    if isinstance(a, LogicConst) and isinstance(b, LogicConst):
        return LogicConst(a.value ^ b.value)
    if isinstance(b, LogicConst) and b.value == 0: return a
    if isinstance(a, LogicConst) and a.value == 0: return b
    if isinstance(b, LogicConst) and b.value == 1: return simplify(NotOp(a))
    if isinstance(a, LogicConst) and a.value == 1: return simplify(NotOp(b))
    if isinstance(a, XorOp) and isinstance(b, LogicConst) and b.value == 1:
        inner = simplify(a)
        if isinstance(inner.b, LogicConst) and inner.b.value == 1:
            return simplify(inner.a)
    return XorOp(a, b)

@simplify.register(XnorOp)
def _(node: XnorOp) -> LogicTreeNode:
    a = simplify(node.a)
    b = simplify(node.b)
    if isinstance(a, LogicConst) and isinstance(b, LogicConst):
        return LogicConst(int(not (a.value ^ b.value)))
    if a.equals(b):
        return LogicConst(1)
    if isinstance(b, LogicConst):
        if b.value == 0: return simplify(NotOp(a))
        if b.value == 1: return a
    if isinstance(a, LogicConst):
        if a.value == 0: return simplify(NotOp(b))
        if a.value == 1: return b
    return XnorOp(a, b)

@simplify.register(NandOp)
def _(node: NandOp) -> LogicTreeNode:
    a = simplify(node.a)
    b = simplify(node.b)
    if isinstance(a, LogicConst):
        if a.value == 0: return LogicConst(1)
        if a.value == 1: return simplify(NotOp(b))
    if isinstance(b, LogicConst):
        if b.value == 0: return LogicConst(1)
        if b.value == 1: return simplify(NotOp(a))
    if a.equals(b):
        return simplify(NotOp(a))
    return NandOp(a, b)

@simplify.register(NorOp)
def _(node: NorOp) -> LogicTreeNode:
    a = simplify(node.a)
    b = simplify(node.b)
    if isinstance(a, LogicConst):
        if a.value == 1: return LogicConst(0)
        if a.value == 0: return simplify(NotOp(b))
    if isinstance(b, LogicConst):
        if b.value == 1: return LogicConst(0)
        if b.value == 0: return simplify(NotOp(a))
    if a.equals(b):
        return simplify(NotOp(a))
    return NorOp(a, b)

@simplify.register
def _(node: LogicVar): return node

@simplify.register
def _(node: LogicConst): return node

simplify_logic_tree = simplify
#@singledispatch
#def simplify(node):
#    return node  # default fallback
#
#@simplify.register(NotOp)
#def _(node: NotOp) -> LogicTreeNode:
#    operand = simplify_logic_tree(node.operand)
#
#    # Double negation: ~~a → a
#    if isinstance(operand, NotOp):
#        return operand.operand
#
#    # Constant inversion
#    if isinstance(operand, LogicConst):
#        return LogicConst(1 - operand.value)
#
#    return NotOp(operand)
#
#@simplify.register
#def _(node: AndOp):
#    a = simplify(node.a)
#    b = simplify(node.b)
#    if isinstance(a, LogicConst) and a.value == 0 or isinstance(b, LogicConst) and b.value == 0:
#        return LogicConst(0)
#    if isinstance(a, LogicConst) and a.value == 1:
#        return b
#    if isinstance(b, LogicConst) and b.value == 1:
#        return a
#    return AndOp(a, b)
#
#@simplify.register
#def _(node: OrOp):
#    a = simplify(node.a)
#    b = simplify(node.b)
#    if isinstance(a, LogicConst) and a.value == 1 or isinstance(b, LogicConst) and b.value == 1:
#        return LogicConst(1)
#    if isinstance(a, LogicConst) and a.value == 0:
#        return b
#    if isinstance(b, LogicConst) and b.value == 0:
#        return a
#    return OrOp(a, b)
#
#@simplify.register(XorOp)
#def _(node: XorOp) -> LogicTreeNode:
#    a = simplify_logic_tree(node.a)
#    b = simplify_logic_tree(node.b)
#
#    # Constant folding
#    if isinstance(a, LogicConst) and isinstance(b, LogicConst):
#        return LogicConst(a.value ^ b.value)
#
#    # Identity: a ^ 0 → a
#    if isinstance(b, LogicConst) and b.value == 0:
#        return a
#    if isinstance(a, LogicConst) and a.value == 0:
#        return b
#
#    # Inversion: a ^ 1 → ~a
#    if isinstance(b, LogicConst) and b.value == 1:
#        return simplify_logic_tree(NotOp(a))
#    if isinstance(a, LogicConst) and a.value == 1:
#        return simplify_logic_tree(NotOp(b))
#
#    # Double inversion: (a ^ 1) ^ 1 → a
#    if isinstance(a, XorOp) and isinstance(b, LogicConst) and b.value == 1:
#        inner = simplify_logic_tree(a)
#        if isinstance(inner.b, LogicConst) and inner.b.value == 1:
#            return simplify_logic_tree(inner.a)
#
#    return XorOp(a, b)
#
#@simplify.register(XnorOp)
#def _(node: XnorOp) -> LogicTreeNode:
#    a = simplify_logic_tree(node.a)
#    b = simplify_logic_tree(node.b)
#
#    # Constant folding
#    if isinstance(a, LogicConst) and isinstance(b, LogicConst):
#        return LogicConst(int(not (a.value ^ b.value)))
#
#    # Identity: a ~^ a → 1
#    if a.equals(b):
#        return LogicConst(1)
#
#    # Constant-based simplification
#    if isinstance(b, LogicConst):
#        if b.value == 0:
#            return simplify_logic_tree(NotOp(a))  # a ~^ 0 → ~a
#        elif b.value == 1:
#            return a                             # a ~^ 1 → a
#    if isinstance(a, LogicConst):
#        if a.value == 0:
#            return simplify_logic_tree(NotOp(b))
#        elif a.value == 1:
#            return b
#
#    return XnorOp(a, b)
#
#@simplify.register(NandOp)
#def _(node: NandOp) -> LogicTreeNode:
#    a, b = node.a, node.b
#    if isinstance(a, LogicConst):
#        if a.value == 0: return LogicConst(1)
#        if a.value == 1: return NotOp(b)
#    if isinstance(b, LogicConst):
#        if b.value == 0: return LogicConst(1)
#        if b.value == 1: return NotOp(a)
#    if a.equals(b):
#        return NotOp(a)
#    return node
#
#@simplify.register(NorOp)
#def _(node: NorOp) -> LogicTreeNode:
#    a, b = node.a, node.b
#    if isinstance(a, LogicConst):
#        if a.value == 1: return LogicConst(0)
#        if a.value == 0: return NotOp(b)
#    if isinstance(b, LogicConst):
#        if b.value == 1: return LogicConst(0)
#        if b.value == 0: return NotOp(a)
#    if a.equals(b):
#        return NotOp(a)
#    return node
#
#@simplify.register
#def _(node: LogicVar):
#    return node
#
#@simplify.register
#def _(node: LogicConst):
#    return node
#
#simplify_logic_tree = simplify
