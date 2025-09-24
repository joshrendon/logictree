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


@singledispatch
def depth(node: LogicTreeNode) -> int:
    raise NotImplementedError(f"No depth() for {type(node)}")


# --- Leaves ---
@depth.register
def _(node: LogicVar) -> int: return 0

@depth.register
def _(node: LogicConst) -> int: return 0

@depth.register
def _(node: EmptyBranch) -> int: return 0

@depth.register
def _(node: LogicHole) -> int: return 0


# --- Unary op ---
@depth.register
def _(node: NotOp) -> int:
    return 1 + depth(node.operands[0])


# --- N-ary ops ---
@depth.register(AndOp)
@depth.register(OrOp)
@depth.register(XorOp)
@depth.register(XnorOp)
@depth.register(NandOp)
@depth.register(NorOp)
@depth.register(EqOp)
@depth.register(NeqOp)
def _(node) -> int:
    return 1 + max((depth(c) for c in node.operands), default=0)


# --- Mux ---
@depth.register
def _(node: LogicMux) -> int:
    # selector doesn't add depth
    return 1 + max(depth(c) for c in node.operands)

#def depth(self) -> int:
#    inputs = [self.if_true, self.if_false]
#    input_depths = [inp.depth for inp in inputs if inp]
#    sel_depth = self.selector.depth if self.selector else 0
#    return 1 + max(input_depths + [sel_depth], default=0)


# --- Selects ---
@depth.register
def _(node: BitSelect) -> int:
    return max((depth(c) for c in node.operands), default=0)

@depth.register
def _(node: PartSelect) -> int:
    return max((depth(c) for c in node.operands), default=0)

@depth.register
def _(node: Concat) -> int:
    return max((depth(c) for c in node.operands), default=0)

#@depth.register(BitSelect)
#@depth.register(PartSelect)
#@depth.register(Concat)
#def _(node) -> int:
#    return max((depth(c) for c in node.operands), default=0)


# --- Control ---
@depth.register
def _(node: LogicAssign) -> int:
    return depth(node.rhs)

@depth.register
def _(node: IfStatement) -> int:
    return 1 + max(depth(node.then_branch), depth(node.else_branch))

@depth.register
def _(node: CaseItem) -> int:
    return 1 + max((depth(ch) for ch in node.children), default=0)

@depth.register
def _(node: CaseStatement) -> int:
    return 1 + max((depth(ci) for ci in node.items), default=0)

@depth.register
def _(node: BlockStatement) -> int:
    return max((depth(s) for s in node.statements), default=0)


# --- Structural Module ---
@depth.register
def _(node: Module) -> int:
    return max((depth(s) for s in node.assignments), default=0)
