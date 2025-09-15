# src/logictree/transforms/to_primitives.py
from functools import singledispatch

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.selects import BitSelect


@singledispatch
def to_primitives(node: LogicTreeNode) -> LogicTreeNode:
    return node


@to_primitives.register
def _(node: LogicConst):
    return node


@to_primitives.register
def _(node: LogicVar):
    return node

@to_primitives.register
def _(node: EqOp):
    # Only handle bit-to-const comparisons
    if isinstance(node.lhs, BitSelect) and isinstance(node.rhs, LogicConst):
        bit = node.lhs
        const = node.rhs
    elif isinstance(node.rhs, BitSelect) and isinstance(node.lhs, LogicConst):
        bit = node.rhs
        const = node.lhs
    else:
        return EqOp(to_primitives(node.lhs), to_primitives(node.rhs))

    if const.value == 1:
        return to_primitives(bit)
    elif const.value == 0:
        return NotOp(to_primitives(bit))
    else:
        raise ValueError(f"Unsupported EqOp const value: {const.value}")

@to_primitives.register
def _(node: NeqOp):
    return NotOp(to_primitives(EqOp(node.lhs, node.rhs)))

@to_primitives.register
def _(node: NotOp):
    return NotOp(to_primitives(node.operand))


@to_primitives.register

def _(node: AndOp):
    return AndOp(to_primitives(node.a), to_primitives(node.b))


@to_primitives.register

def _(node: OrOp):
    return OrOp(to_primitives(node.a), to_primitives(node.b))


@to_primitives.register

def _(node: NandOp):
    a = to_primitives(node.a)
    b = to_primitives(node.b)
    return NotOp(AndOp(a, b))


@to_primitives.register

def _(node: NorOp):
    a = to_primitives(node.a)
    b = to_primitives(node.b)
    return NotOp(OrOp(a, b))


@to_primitives.register

def _(node: XorOp):
    a = to_primitives(node.a)
    b = to_primitives(node.b)
    return OrOp(
        AndOp(a, NotOp(b)),
        AndOp(NotOp(a), b),
    )


@to_primitives.register

def _(node: XnorOp):
    a = to_primitives(node.a)
    b = to_primitives(node.b)
    return NotOp(to_primitives(XorOp(a, b)))


@to_primitives.register

def _(node: LogicMux):
    sel = to_primitives(node.selector)
    a = to_primitives(node.if_true)
    b = to_primitives(node.if_false)
    return OrOp(
        AndOp(sel, a),
        AndOp(NotOp(sel), b)
    )


to_primitives_logic_tree = to_primitives
