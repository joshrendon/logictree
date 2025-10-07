from functools import singledispatch

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module
from logictree.nodes.struct.statement import BlockStatement
from logictree.nodes.ops.ite import ITEOp


@singledispatch
def delay(node: LogicTreeNode) -> int:
    raise NotImplementedError(f"No delay() for {type(node)}")


# --- Leaves ---
@delay.register(LogicVar)
@delay.register(LogicConst)
@delay.register(LogicHole)
@delay.register(EmptyBranch)
def _(node) -> int:
    return 0


# --- Unary ---
@delay.register
def _(node: NotOp) -> int:
    return 1 + delay(node.operands[0])


# --- Binary / N-ary ops ---
@delay.register(AndOp)
@delay.register(OrOp)
@delay.register(XorOp)
@delay.register(XnorOp)
@delay.register(NandOp)
@delay.register(NorOp)
@delay.register(EqOp)
@delay.register(NeqOp)
def _(node) -> int:
    return 1 + max((delay(c) for c in node.operands), default=0)


# --- Mux ---
@delay.register
def _(node: LogicMux) -> int:
    return 1 + max(delay(c) for c in node.operands)


# --- Selects ---
@delay.register(BitSelect)
@delay.register(PartSelect)
@delay.register(Concat)
def _(node) -> int:
    return max((delay(c) for c in node.operands), default=0)


# --- Control ---
@delay.register
def _(node: LogicAssign) -> int:
    return delay(node.rhs)

@delay.register
def _(node: IfStatement) -> int:
    return 1 + max(delay(node.then_branch), delay(node.else_branch))

@delay.register
def _(node: CaseItem) -> int:
    return 1 + max((delay(ch) for ch in node.children), default=0)

@delay.register
def _(node: CaseStatement) -> int:
    return 1 + max((delay(ci) for ci in node.items), default=0)

@delay.register
def _(node: BlockStatement) -> int:
    return max((delay(s) for s in node.statements), default=0)

@delay.register
def _(node: ITEOp) -> int:
    # 1 + max delay of operands (like a mux)
    return 1 + max((delay(op) for op in node.children), default=0)

# --- Module ---
@delay.register
def _(node: Module) -> int:
    return max((delay(s) for s in node.assignments), default=0)
