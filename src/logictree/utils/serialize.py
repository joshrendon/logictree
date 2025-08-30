import json
import logging

from logictree.nodes.control.assign import LogicAssign
from logictree.utils.overlay import get_label

log = logging.getLogger(__name__)


def logic_tree_to_json(tree):
    def safe_label(x):
        if x is None:
            return None
        try:
            return get_label(x)
        except Exception:
            return str(x)

    def serialize_node(node):
        node_type = node.__class__.__name__

        # Handle IfStatement
        if node_type == "IfStatement":
            children = []
            if node.then_branch:
                children.append(
                    {
                        "type": "ThenBranch",
                        "label": "then",
                        "children": [serialize_node(node.then_branch)],
                    }
                )
            if node.else_branch:
                children.append(
                    {
                        "type": "ElseBranch",
                        "label": "else",
                        "children": [serialize_node(node.else_branch)],
                    }
                )
            return {
                "type": node_type,
                "label": safe_label(node),
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children,
            }

        # Handle FlattenedIfStatement
        elif node_type == "FlattenedIfStatement":
            children = []
            children.append(
                {
                    "type": "IfCondition",
                    "label": f"if({safe_label(node.cond)})",
                    "children": [serialize_node(node.then_branch)],
                }
            )
            for cond, branch in node.else_if_branches:
                children.append(
                    {
                        "type": "ElseIfCondition",
                        "label": f"else if({safe_label(cond)})",
                        "children": [serialize_node(branch)],
                    }
                )
            if node.else_branch:
                children.append(
                    {
                        "type": "ElseCondition",
                        "label": "else",
                        "children": [serialize_node(node.else_branch)],
                    }
                )
            return {
                "type": node_type,
                "label": safe_label(node),
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children,
            }

        # Handle CaseStatement
        elif node_type == "CaseStatement":
            children = []
            if hasattr(node, "selector"):
                children.append(
                    {
                        "type": "Selector",
                        "label": f"selector = {safe_label(node.selector)}",
                        "children": [serialize_node(node.selector)],
                    }
                )
            for case_item in getattr(node, "items", []):
                case_labels = getattr(case_item, "labels", [])
                case_label_str = ", ".join(safe_label(lbl) for lbl in case_labels)
                children.append(
                    {
                        "type": "CaseItem",
                        "label": f"case {case_label_str}",
                        "children": [serialize_node(case_item.body)],
                    }
                )
            return {
                "type": node_type,
                "label": safe_label(node),
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children,
            }

        # Handle LogicAssign
        elif isinstance(node, LogicAssign):
            return {
                "type": "LogicAssign",
                "label": f"{node.lhs} = {safe_label(node.rhs)}",
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": [serialize_node(node.rhs)] if node.rhs else [],
            }

        # Fallback serialization
        return {
            "type": node_type,
            "label": safe_label(node),
            "depth": getattr(node, "depth", None),
            "delay": getattr(node, "delay", None),
            "expr_source": getattr(node, "expr_source", None),
            "children": [
                serialize_node(child)
                for child in getattr(node, "children", [])
                if child is not None
            ],
        }

    json_data = serialize_node(tree)

    try:
        log.info("Serialize JSON: %s", json.dumps(json_data, indent=2))
    except TypeError as e:
        log.info("JSON serialization failed: %s", e)
        log.info("Offending object (raw): %s", json_data)

    return json_data
