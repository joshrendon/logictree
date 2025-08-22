from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
import json
import logging
log = logging.getLogger(__name__)

def logic_tree_to_json(tree):
    def safe_label(x):
        if x is None:
            return None
        label_attr = getattr(x, "label", None)
        if callable(label_attr):
            return label_attr()
        return str(label_attr) if label_attr is not None else str(x)

    def serialize_node(node):
        node_type = node.__class__.__name__
        label = safe_label(node)

        # Handle CaseStatement specially
        if node_type == "IfStatement":
            children = []
        
            if node.then_branch:
                children.append({
                    "type": "ThenBranch",
                    "label": "then",
                    "children": [serialize_node(node.then_branch)]
                })
        
            if node.else_branch:
                children.append({
                    "type": "ElseBranch",
                    "label": "else",
                    "children": [serialize_node(node.else_branch)]
                })
        
            return {
                "type": "IfStatement",
                "label": node.label(),
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children
            }
            #if getattr(node, "_is_else_if", False):
            #    #label = f"else if({safe_label(node.condition)})"
            #    label = f"else if({safe_label(node.cond)})"
            #else:
            #    label = f"if({safe_label(node.cond)})"
            label = node.label()

        elif node_type == "FlattenedIfStatement":
            children = []
        
            # Always append the first "if"
            children.append({
                "type": "IfCondition",
                "label": f"if({safe_label(node.cond)})",
                "children": [serialize_node(node.then_branch)]
            })
        
            # Append all "else if"s
            for cond, branch in node.else_if_branches:
                children.append({
                    "type": "ElseIfCondition",
                    "label": f"else if({safe_label(cond)})",
                    "children": [serialize_node(branch)]
                })
        
            # Append optional "else"
            if node.else_branch:
                children.append({
                    "type": "ElseCondition",
                    "label": "else",
                    "children": [serialize_node(node.else_branch)]
                })
        
            return {
                "type": node_type,
                "label": label(),
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children
            }

        elif node_type == "CaseStatement":
            children = []

            # Add selector as its own labeled child
            if hasattr(node, "selector"):
                children.append({
                    "type": "Selector",
                    "label": f"selector = {safe_label(node.selector)}",
                    "children": [serialize_node(node.selector)]
                })

            # Each CaseItem as its own subtree
            for case_item in getattr(node, "items", []):
                case_labels = getattr(case_item, "labels", [])
                case_label_str = ", ".join(safe_label(lbl) for lbl in case_labels)
                children.append({
                    "type": "CaseItem",
                    "label": f"case {case_label_str}",
                    "children": [serialize_node(case_item.body)]
                })

            return {
                "type": node_type,
                "label": label,
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": children
            }
        elif isinstance(node, LogicAssign):
            return {
                "type": "LogicAssign",
                "label": f"{node.lhs} = {safe_label(node.rhs)}",
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": [serialize_node(node.rhs)] if node.rhs else [],
            }
        else:
            # Fallback for any node type not handled explicitly
            label = safe_label(node)
            #if child is None:
            #    log.warning(f"serialize_node got None child for parent node_type={node_type} label={label}")

        
            return {
                "type": node_type,
                #"label": node.label(),
                "label": label,
                "depth": getattr(node, "depth", None),
                "delay": getattr(node, "delay", None),
                "expr_source": getattr(node, "expr_source", None),
                "children": [
                    serialize_node(child)
                    for child in getattr(node, "children", [])
                    if child is not None
                ]
            }

    json_data = serialize_node(tree)

    # Debug print for verification
    try:
        log.info("Serialize JSON: %s", json.dumps(json_data, indent=2))
    except TypeError as e:
        log.info("JSON serialization failed: %s", e)
        log.info("Offending object (raw): %s", json_data)

    return json_data
