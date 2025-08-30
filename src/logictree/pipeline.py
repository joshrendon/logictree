import logging
from typing import Any, Dict

from logictree.nodes.base.base import LogicTreeNode
from logictree.SVToLogicTreeLowerer import SVToLogicTreeLowerer
from sv_parser.parse import parse_sv_file, parse_sv_text
from sv_parser.SystemVerilogSubsetParser import SystemVerilogSubsetParser

try:
    from logictree.nodes.control.case import CaseItem, CaseStatement
except Exception:
    CaseStatement = CaseItem = None  # fallback if names differ

from logictree.nodes.struct.module import Module

ModuleMap = Dict[str, Module]
log = logging.getLogger(__name__)


def _extract_assign(item: Any) -> tuple[str, LogicTreeNode] | None:
    """
    Try to extract (lhs_name, rhs_expr) from an assignment-like thing:
    - an assignment node with .lhs/.rhs or .target/.rhs
    - a CaseItem whose .body is such an assignment
    """
    # CaseItem → unwrap to its body
    if CaseItem and isinstance(item, CaseItem):
        item = getattr(item, "body", item)

    lhs = getattr(item, "lhs", None) or getattr(item, "target", None)
    rhs = (
        getattr(item, "rhs", None)
        or getattr(item, "value", None)
        or getattr(item, "expr", None)
    )
    if lhs is None or rhs is None:
        return None

    # Derive a stable name for the LHS
    key = getattr(lhs, "name", None) or str(lhs)
    return (str(key), rhs)


def _normalize_case(stmt: Any) -> Dict[str, LogicTreeNode]:
    """
    Turn a CaseStatement into {out_name: rhs_expr} by pulling assignments
    from its items' bodies.
    """
    out: Dict[str, LogicTreeNode] = {}
    items = getattr(stmt, "items", []) or []
    for it in items:
        pair = _extract_assign(it)
        if pair:
            k, v = pair
            out[k] = v
    return out


def _normalize_outputs(selected: Any) -> Dict[str, LogicTreeNode]:
    """
    Coerce various lowerer return shapes into {output_name: LogicTreeNode}.
    Accepts dict, lists/tuples of assigns/CaseItems, single control nodes, etc.
    """
    # Already a dict of exprs
    if isinstance(selected, dict):
        return selected

    # CaseStatement → map of outputs
    if CaseStatement and isinstance(selected, CaseStatement):
        mapped = _normalize_case(selected)
        if mapped:
            return mapped

    out: Dict[str, LogicTreeNode] = {}

    # Sequence forms
    if isinstance(selected, (list, tuple)):
        for item in selected:
            # (“name”, expr) tuples
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str):
                out[item[0]] = item[1]
                continue

            # CaseStatement entries inside lists
            if CaseStatement and isinstance(item, CaseStatement):
                out.update(_normalize_case(item))
                continue

            # assignment-like node
            pair = _extract_assign(item)
            if pair:
                k, v = pair
                out[k] = v
                continue

            # plain expr node as a last resort
            if isinstance(item, LogicTreeNode):
                out.setdefault("out", item)
        return out

    # Single expr node
    if isinstance(selected, LogicTreeNode):
        # If someone passed a raw assignment node by mistake, try to unwrap
        pair = _extract_assign(selected)
        if pair:
            k, v = pair
            return {k: v}
        return {"out": selected}

    # Fallback: unknown shape
    return {"out": selected}


def _lower_module_and_normalize(parse_tree) -> dict:
    """
    Extracts the first module_declaration from the given parse tree,
    lowers it to LogicTree IR using SVToLogicTreeLowerer, and returns
    a map from output signal names to LogicTreeNode instances.

    This does not apply any lowering transformations (e.g., case_to_if),
    nor does it resolve intermediate signal variables.

    Intended for use in unit tests, single-module exploration, and debug tools.
    """
    lowerer = SVToLogicTreeLowerer()

    module_ctx = None
    for child in parse_tree.getChildren():
        if isinstance(child, SystemVerilogSubsetParser.Module_declarationContext):
            module_ctx = child
            break

    if module_ctx is None:
        raise RuntimeError("No module_declaration found in parsed file.")

    selected_tree = lowerer.visitModule_declaration(module_ctx)

    log.debug(f"Returning tree of type: {type(selected_tree).__name__}")
    # Normalize to a signal name → tree map
    return _normalize_outputs(selected_tree)


def _lower_all_modules(parse_tree) -> ModuleMap:
    """
    Extracts all module_declaration nodes from the given parse tree,
    lowers each to LogicTree IR using SVToLogicTreeLowerer, and returns
    a dict mapping module names to Module objects.

    This does not apply any transformations or analysis.
    """
    lowerer = SVToLogicTreeLowerer()
    module_map: ModuleMap = {}

    for child in parse_tree.getChildren():
        if isinstance(child, SystemVerilogSubsetParser.Module_declarationContext):
            mod_obj = lowerer.visitModule_declaration(child)
            if not mod_obj:
                log.warn("lowerer returned no module on vistModule_declaration()")
                continue
            if not hasattr(mod_obj, "name"):
                log.warning("Skipping unnamed or invalid module")
                log.debug(f"mod: type(): {type(mod_obj)} dir: {dir(mod_obj)}")
                log.warn("Skipping module missing .name")
                continue

            module_map[mod_obj.name] = mod_obj

    if not module_map:
        raise RuntimeError("No valid module_declaration found in parsed file.")
    return module_map


def lower_sv_text_to_logic(src: str) -> ModuleMap:
    parse_tree = parse_sv_text(src)
    return _lower_all_modules(parse_tree)


def lower_sv_file_to_logic(path: str) -> ModuleMap:
    parse_tree = parse_sv_file(path)
    return _lower_all_modules(parse_tree)
