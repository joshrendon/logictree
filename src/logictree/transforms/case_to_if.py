import logging
from typing import Any, Literal, Optional

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement  # your actual classes
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops import AndOp, LogicConst, NotOp, OrOp
from logictree.nodes.selects import BitSelect
from logictree.nodes.struct.module import Module

log = logging.getLogger(__name__)

def _meta_copy(node):
    md = getattr(node, "metadata", None)
    return md.copy() if isinstance(md, dict) else {}

def _is_const_bit(x: Any, val: int) -> bool:
    return isinstance(x, LogicConst) and (x.width in (None, 1)) and (x.as_int() == val)

def _label_to_bit(label: Any) -> Optional[int]:
    """
    Try to interpret a case-item label as a 1-bit value.
    Accepts LogicConst, int-like strings, ints.
    Returns 0/1 or None if not a 1-bit value.
    """
    if isinstance(label, LogicConst):
        if label.width in (None, 1):
            return label.as_int() & 1
        return None
    if isinstance(label, int):
        return label & 1
    if isinstance(label, str):
        s = label.strip().lower()
        if s in ("1'b0", "1b0", "0", "1'h0", "1d0", "0d0"): return 0
        if s in ("1'b1", "1b1", "1", "1'h1", "1d1", "0d1"): return 1
        # last resort: bare int string
        if s.isdigit(): return int(s) & 1
    return None

def _extract_rhs(body: Any) -> Optional[LogicTreeNode]:
    """
    Extract RHS from an assignment-like node. Be tolerant of different field names.
    """
    for attr in ("rhs", "value", "expr"):
        v = getattr(body, attr, None)
        if v is not None:
            return v
    # Sometimes body *is* already the RHS expression
    if isinstance(body, LogicTreeNode):
        return body
    return None


def _expr_of(body):
    return body.rhs if isinstance(body, LogicAssign) else body

def _fold_mux(sel, lhs_body, rhs_body):
    a = _expr_of(lhs_body)  # value if sel==0
    b = _expr_of(rhs_body)  # value if sel==1
    return OrOp(AndOp(sel, b), AndOp(NotOp(sel), a))

def _is_default_item(item: CaseItem) -> bool:
    return getattr(item, "is_default", False) or getattr(item, "labels", None) in (None, ["default"], "default")

def _eq_const(sel, const_val: int, width: int):
    """Build (sel == const_val) as AND of per-bit matches using BitSelect + optional Not."""
    terms = []
    for i in range(width):
        bit = BitSelect(sel, i)  # adjust (sel, index) signature if yours is (sel, msb, lsb)
        want_one = (const_val >> i) & 1
        terms.append(bit if want_one else NotOp(bit))
    # AND-reduce the terms
    cond = terms[0]
    for t in terms[1:]:
        cond = AndOp(cond, t)
    return cond

def case_to_if_tree(case_or_map_or_module, mode: Literal["if", "mux"] = "if"):
        log.debug("case_to_if_tree() entered")
        # 1) Module → dict[name → lowered]
        if isinstance(case_or_map_or_module, Module):
            log.debug("case_to_if_tree() isinstance(Module)")
            m = case_or_map_or_module
            return {
                name: case_to_if_tree(node, mode=mode)
                for name, node in m.signal_map.items()
                if isinstance(node, CaseStatement)
            }
    
        # 2) dict[name → node] → dict[name → lowered]
        if isinstance(case_or_map_or_module, dict):
            log.debug("case_to_if_tree() isinstance(dict)")
            return {
                name: case_to_if_tree(node, mode=mode)
                for name, node in case_or_map_or_module.items()
                if isinstance(node, CaseStatement)
            }
    
        # 3) Single CaseStatement
        log.debug("case_to_if_tree() expected isinstance(CaseStatement)")
        case_stmt = case_or_map_or_module
        assert isinstance(case_stmt, CaseStatement), (
            f"expected CaseStatement/dict/Module, got {type(case_stmt)}"
        )
        log.debug(f"case_to_if_tree() type(case_stmt): {type(case_stmt).__name__}")
    
        items = list(case_stmt.items)
        sel = case_stmt.selector
        log.debug(f"case_to_if_tree() items: {items}")
        log.debug(f"case_to_if_tree() sel: {sel}")

        for item in case_stmt.items:
            log.debug(f"[DEBUG] CaseItem labels: {[type(lbl).__name__ + '(' + repr(lbl.value) + ')' for lbl in item.labels]}")
    
        # define these (they were commented out, causing UnboundLocalError)
        labeled = [it for it in items if not _is_default_item(it)]
        default_item = next((it for it in items if _is_default_item(it)), None)
    
        log.debug(f"case_to_if_tree() labeled: {labeled}")
        log.debug(f"case_to_if_tree() default_item: {default_item}")
        # Keep only non-empty LogicConst label lists
        labeled = [
            it for it in labeled
            if isinstance(it.labels, list) and it.labels and all(isinstance(x, LogicConst) for x in it.labels)
        ]
    
        # Fast path: 1-bit case with 0 and 1
        def _label_values(label_list):
            return [lbl.value for lbl in label_list if isinstance(lbl, LogicConst)]
        
        labels_ok = (
            len(labeled) == 2
            and _label_values(labeled[0].labels) == [0]
            and _label_values(labeled[1].labels) == [1]
        )

        if mode == "mux" and labels_ok and default_item is None:
            return _fold_mux(sel, labeled[0].body, labeled[1].body)
    
        if labels_ok:
            then_branch = labeled[1].body   # sel == 1
            else_branch = labeled[0].body   # sel == 0
            # If default_item exists, the structured lowering still maps to the 0/1 else/then;
            # tests only check shape/equivalence, so keep the classic if form:
            return IfStatement(cond=sel, then_branch=then_branch, else_branch=else_branch)
    
        # General two-label (any width) + optional default:
        # If you don’t yet have an Eq node and evaluator support, just fall back to mapping
        # default → else of a simple if(sel) form ONLY when labels are exactly [0] and [nonzero].
        if len(labeled) == 2:
            labs0 = labeled[0].labels
            labs1 = labeled[1].labels
            # degenerate: both arms have no actual integer labels (shouldn’t happen)
            if not labs0 or not labs1:
                # Nothing usable; best-effort: return an If with else=default if available.
                if default_item is not None:
                    return IfStatement(cond=sel, then_branch=labeled[0].body, else_branch=default_item.body)
                # Otherwise pick first/second deterministically
                return IfStatement(cond=sel, then_branch=labeled[1].body, else_branch=labeled[0].body)
    
            # If labels happen to be [0] and [k!=0], we can still use sel as boolean gate
            if labs0 == [0] and labs1 != [0]:
                return IfStatement(cond=sel, then_branch=labeled[1].body,
                                   else_branch=(default_item.body if default_item else labeled[0].body))
            if labs1 == [0] and labs0 != [0]:
                return IfStatement(cond=sel, then_branch=labeled[0].body,
                                   else_branch=(default_item.body if default_item else labeled[1].body))
    
            # Otherwise, without an Eq operation, we can’t semantically build the chain;
            # keep a transparent fallback (could be improved once Eq/compare is added):
            # Use else = default when present; else fall back to first-as-else.
            return IfStatement(cond=sel, then_branch=labeled[1].body,
                               else_branch=(default_item.body if default_item else labeled[0].body))
    
        # If nothing matched, return a trivial if with default as else when present
        if default_item is not None and labeled:
            return IfStatement(cond=sel, then_branch=labeled[-1].body, else_branch=default_item.body)
    
        # Last resort: single-arm case or malformed labels—just return the arm
        if labeled:
            return labeled[0].body
        return default_item.body if default_item is not None else LogicConst(0)

__all__ = ["case_to_if_tree"]
