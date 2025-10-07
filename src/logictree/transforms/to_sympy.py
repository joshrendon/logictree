import re
import sympy as sympy
from rich.console import Console
from rich.text import Text
from sympy import Piecewise, S, symbols, true

from logictree.nodes.control.assign import LogicAssign, ContinuousAssign, ProceduralAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module
from logictree.nodes.struct.statement import BlockStatement
from logictree.nodes.control.alwaysblock import AlwaysBlock
from logictree.nodes.ops.ite import ITEOp

import logging
log = logging.getLogger(__name__)


def to_sympy_expr(tree):
    if isinstance(tree, LogicVar):
        return symbols(tree.name)
    elif isinstance(tree, LogicConst):
        return int(tree.value)
    elif isinstance(tree, EmptyBranch):
        # Treat as 0 (False) for equivalence checking
        return S.false
    elif isinstance(tree, AndOp):
        return to_sympy_expr(tree.operands[0]) & to_sympy_expr(tree.operands[1])
    elif isinstance(tree, OrOp):
        return to_sympy_expr(tree.operands[0]) | to_sympy_expr(tree.operands[1])
    elif isinstance(tree, NotOp):
        return not(to_sympy_expr(tree.operand))
    elif isinstance(tree, EqOp):
        return to_sympy_expr(tree.lhs) == to_sympy_expr(tree.rhs)
    elif isinstance(tree, IfStatement):
        return Piecewise(
            (to_sympy_expr(tree.then_branch), to_sympy_expr(tree.cond)),
            (to_sympy_expr(tree.else_branch), True)
        )
    elif isinstance(tree, ITEOp):
        cond = to_sympy_expr(tree.cond)
        tval = to_sympy_expr(tree.if_true)
        fval = to_sympy_expr(tree.if_false)
        return Piecewise((tval,cond), (fval, true))
    elif isinstance(tree, LogicMux):
        sel = to_sympy_expr(tree.selector)
        if_true = to_sympy_expr(tree.if_true)
        if_false = to_sympy_expr(tree.if_false)
        return Piecewise((if_true, sel), (if_false, True))
    elif isinstance(tree, BitSelect):
        # Treat like a variable with subscript notation: sel[0] becomes Symbol("sel_0")
        var = to_sympy_expr(tree.base)
        idx = to_sympy_expr(tree.index)
        return symbols(f"{var}_{idx}")
    elif isinstance(tree, PartSelect):
        var = to_sympy_expr(tree.base)
        msb = to_sympy_expr(tree.msb)
        lsb = to_sympy_expr(tree.lsb)
        return symbols(f"{var}_{msb}_{lsb}")
    elif isinstance(tree, Concat):
        parts = [to_sympy_expr(p) for p in tree.parts]
        return sum(p << (i * len(bin(p))-2) for i, p in enumerate(reversed(parts)))
    elif isinstance(tree, LogicAssign):
        return to_sympy_expr(tree.rhs)
    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")
