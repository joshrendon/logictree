import logging

import sympy as sympy
from sympy import And, Integer, Not, Or, Piecewise, S, Symbol, symbols

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.ite import ITEOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.statement import BlockStatement

log = logging.getLogger(__name__)

def _to_bool_const(c: int):
    """Convert int constants to Boolean constants for width==1 signals."""
    return S.true if c else S.false

def _coerce_eq_to_bool(lhs, rhs):
    """
    Coerce an equality comparison into Boolean form.
    - If comparing Boolean signals with 0/1 or True/False, return sel/~sel.
    - If comparing identical symbols, return True.
    - Fallback: return a new Boolean symbol rather than Eq().
    """
    # Normalize common constants
    if rhs in (S.true, True, 1):
        return lhs
    if rhs in (S.false, False, 0):
        return Not(lhs)
    if lhs in (S.true, True, 1):
        return rhs
    if lhs in (S.false, False, 0):
        return Not(rhs)

    # If both are Boolean and identical, True
    if lhs == rhs:
        return S.true

    # If it’s not a simple Boolean equality (multi-bit compare), represent it symbolically
    name = f"eq_{getattr(lhs, 'name', str(lhs))}_{getattr(rhs, 'name', str(rhs))}"
    return symbols(name, boolean=True)

def to_sympy_expr(tree):
    if isinstance(tree, LogicVar):
        return symbols(tree.name, boolean=True)
    elif isinstance(tree, LogicConst):
        w = getattr(tree, "width", 1)
        v = int(tree.value)
        log.info("tree is LogicConst")
        log.info(f"tree: {tree}")
        log.info(f"tree.width: {w}")
        return Integer(v)
    elif isinstance(tree, EmptyBranch):
        # Treat as 0 (False) for equivalence checking
        return S.false
    elif isinstance(tree, AndOp):
        return to_sympy_expr(tree.operands[0]) & to_sympy_expr(tree.operands[1])
    elif isinstance(tree, OrOp):
        return to_sympy_expr(tree.operands[0]) | to_sympy_expr(tree.operands[1])
    elif isinstance(tree, NotOp):
        return Not(to_sympy_expr(tree.operand))
    elif isinstance(tree, EqOp):
        l = to_sympy_expr(tree.lhs)
        r = to_sympy_expr(tree.rhs)
        return _coerce_eq_to_bool(l, r)
        #return to_sympy_expr(tree.lhs) == to_sympy_expr(tree.rhs)
    elif isinstance(tree, NeqOp):
        return to_sympy_expr(tree.lhs) != to_sympy_expr(tree.rhs)
    elif isinstance(tree, IfStatement):
        #return ITE(tree.cond, tree.then_branch, tree.else_branch)
        #return Or(And(to_sympy_expr(tree.cond), to_sympy_expr(tree.then_branch)),
        #          And(Not(to_sympy_expr(tree.cond)), to_sympy_expr(tree.else_branch)))
        # Piecewise or Boolean mux; Boolean form is easiest for XOR-based checks
        return Piecewise(
            (to_sympy_expr(tree.then_branch), to_sympy_expr(tree.cond)),
            (to_sympy_expr(tree.else_branch), True)
        )
    elif isinstance(tree, BlockStatement):
        # A BlockStatement holds a sequence of statements or expressions.
        # For symbolic equivalence, evaluate the last one that produces a value.
        if not getattr(tree, "statements", None):
            return S.false
        # Evaluate all children to catch nested structures
        subexprs = [to_sympy_expr(stmt) for stmt in tree.statements if stmt is not None]
        if not subexprs:
            return S.false
        return subexprs[-1]

    elif isinstance(tree, CaseStatement):
        # Represent a case statement as a Boolean disjunction of (cond ∧ body)
        sel = to_sympy_expr(tree.selector)
    
        def eq_to_bool(sel_sym, val_expr):
            """Coerce selector==label into a pure Boolean predicate."""
            # Normalize basic constants
            if val_expr is True:  val_expr = S.true
            if val_expr is False: val_expr = S.false
    
            # If the selector itself is Boolean, fold 0/1 or True/False directly
            if getattr(sel_sym, "is_Boolean", False):
                if val_expr in (S.true, True, 1):
                    return sel_sym
                if val_expr in (S.false, False, 0):
                    return Not(sel_sym)
    
            # Handle numeric or Boolean constant labels for non-Boolean selectors
            if val_expr in (0, S.false, False):
                return Not(sel_sym)
            if val_expr in (1, S.true, True):
                return sel_sym
    
            # For multi-bit or symbolic labels, introduce a Boolean match variable
            name = f"match_{getattr(sel_sym, 'name', sel_sym)}_{val_expr}"
            return symbols(name, boolean=True)
    
        expr = S.false
        seen_conds = []
    
        for item in tree.items:
            # Convert label(s) to conditions
            labels = item.labels if isinstance(item.labels, (list, tuple)) else [item.labels]
            conds = [eq_to_bool(sel, to_sympy_expr(lbl)) for lbl in labels]
            cond = Or(*conds) if len(conds) > 1 else conds[0]
    
            seen_conds.append(cond)
    
            # Combine condition with the case body
            body_expr = to_sympy_expr(item.body)
            expr = Or(expr, And(cond, body_expr))
    
        # Handle default case: execute when no previous condition matched
        if getattr(tree, "default", None) is not None:
            guard = Not(Or(*seen_conds)) if seen_conds else S.true
            expr = Or(expr, And(guard, to_sympy_expr(tree.default)))
    
        return expr
    elif isinstance(tree, ITEOp):
        cond = to_sympy_expr(tree.cond)
        tval = to_sympy_expr(tree.if_true)
        fval = to_sympy_expr(tree.if_false)

        if isinstance(fval, Piecewise):
            return Piecewise((tval, cond), *fval.args)
        elif isinstance(tree.if_false, ITEOp):
            inner_pw = to_sympy_expr(tree.if_false)
            return Piecewise((tval, cond), *inner_pw.args)
        else:
            return Piecewise((tval,cond), (fval, S.true))
    elif isinstance(tree, LogicMux):
        sel = to_sympy_expr(tree.selector)
        t   = to_sympy_expr(tree.if_true)
        f   = to_sympy_expr(tree.if_false)
        expr = Or(And(sel, t), And(Not(sel), f))
        log.info(f"expr: {expr}")
        return expr
        #return Piecewise((if_true, sel), (if_false, True))
    elif isinstance(tree, BitSelect):
        # Treat like a variable with subscript notation: sel[0] becomes Symbol("sel_0")
        base = to_sympy_expr(tree.base)
        idx = to_sympy_expr(tree.index)
        # flatten the base name for readability
        base_name = base.name if isinstance(base, Symbol) else str(base)
        return symbols(f"{base_name}_{idx}", bolean=True)
    elif isinstance(tree, PartSelect):
        base = to_sympy_expr(tree.base)
        msb = to_sympy_expr(tree.msb)
        lsb = to_sympy_expr(tree.lsb)
        base_name = base.name if isinstance(base, Symbol) else str(base)
        return symbols(f"{base_name}_{msb}_{lsb}")
    elif isinstance(tree, Concat):
        parts = [to_sympy_expr(p) for p in tree.parts]
        return sum(p << (i * len(bin(p))-2) for i, p in enumerate(reversed(parts)))
    elif isinstance(tree, LogicAssign):
        return to_sympy_expr(tree.rhs)
    # Fallback for Possible bool type
    elif isinstance(tree, bool):
        return S.One if tree else S.Zero
    else:
        raise TypeError(f"Unsupported node type: {type(tree)}")
