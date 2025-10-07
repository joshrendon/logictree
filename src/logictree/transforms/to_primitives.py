# src/logictree/transforms/to_primitives.py
from functools import singledispatch

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicConst, LogicVar
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.selects import BitSelect, Concat
from logictree.nodes.ops.ite import ITEOp


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

#@to_primitives.register
#def _(node: ITEOp):
#    # ITE(c, t, f) → (c & t) | (~c & f)
#    c = to_primitives(node.cond)
#    t = to_primitives(node.if_true)
#    f = to_primitives(node.if_false)
#    return OrOp(
#        AndOp(c, t),
#        AndOp(NotOp(c), f)
#    )

@to_primitives.register
def _(node: ITEOp):
    cond = to_primitives_logic_tree(node.cond)
    t = to_primitives_logic_tree(node.if_true)
    f = to_primitives_logic_tree(node.if_false)

    # normalize to per-bit vectors
    def as_bitlist(x, width):
        if isinstance(x, LogicConst):
            return [(x.value >> i) & 1 for i in range(width)]
        elif isinstance(x, list):
            return x  # already list of bit exprs
        else:
            return [x] * width

    # compute max width
    width = 1
    if isinstance(node.if_true, LogicConst):
        width = max(width, node.if_true.width or 1)
    if isinstance(node.if_false, LogicConst):
        width = max(width, node.if_false.width or 1)

    t_bits = as_bitlist(t, width)
    f_bits = as_bitlist(f, width)

    bit_exprs = []
    for i in range(width):
        t_bit = t_bits[i]
        f_bit = f_bits[i]

        if isinstance(t_bit, int):
            t_bit = LogicConst(t_bit)
        if isinstance(f_bit, int):
            f_bit = LogicConst(f_bit)

        bit_expr = OrOp(
            AndOp(cond, t_bit),
            AndOp(NotOp(cond), f_bit),
        )
        bit_exprs.append(bit_expr)

    return bit_exprs if width > 1 else bit_exprs[0]
#def _(node: ITEOp):
#    """
#    Lower ITEOp(cond, if_true, if_false) into primitive boolean equations.
#    Handles multi-bit constants by expanding into per-bit equations.
#    """
#    cond = to_primitives_logic_tree(node.cond)
#    t = to_primitives_logic_tree(node.if_true)
#    f = to_primitives_logic_tree(node.if_false)
#
#    # Case 1: multi-bit constant in the true branch
#    if isinstance(node.if_true, LogicConst) and node.if_true.width > 1:
#        bits = []
#        for i in range(node.if_true.width):
#            bit_val = (node.if_true.value >> i) & 1
#            bit_const = LogicConst(bit_val)
#            bits.append(OrOp(
#                AndOp(cond, bit_const),
#                AndOp(NotOp(cond), LogicConst(0))  # false path = 0
#            ))
#        return Concat(bits)   # or however your IR encodes vectors
#
#    # Case 2: multi-bit constant in the false branch
#    if isinstance(node.if_false, LogicConst) and node.if_false.width > 1:
#        bits = []
#        for i in range(node.if_false.width):
#            bit_val = (node.if_false.value >> i) & 1
#            bit_const = LogicConst(bit_val)
#            bits.append(OrOp(
#                AndOp(cond, LogicConst(0)),        # true path = 0
#                AndOp(NotOp(cond), bit_const)
#            ))
#        return Concat(bits)
#
#    # Case 3: both branches are multi-bit constants
#    if (isinstance(node.if_true, LogicConst) and node.if_true.width > 1 and
#        isinstance(node.if_false, LogicConst) and node.if_false.width > 1):
#
#        assert node.if_true.width == node.if_false.width, \
#            "ITEOp mismatch: true/false constants must be same width"
#        bits = []
#        for i in range(node.if_true.width):
#            t_bit = LogicConst((node.if_true.value >> i) & 1)
#            f_bit = LogicConst((node.if_false.value >> i) & 1)
#            bits.append(OrOp(
#                AndOp(cond, t_bit),
#                AndOp(NotOp(cond), f_bit)
#            ))
#        return Concat(bits)
#
#    # Default case: single-bit or non-constant branches
#    return OrOp(
#        AndOp(cond, t),
#        AndOp(NotOp(cond), f)
#    )

to_primitives_logic_tree = to_primitives
