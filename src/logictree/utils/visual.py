# logictree/utils/visual.py
from .overlay import set_label
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.case import CaseStatement
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.empty import EmptyBranch

def annotate_mux_node(node):
    sel = node.selector.label() if hasattr(node, "selector") else "?"
    set_label(node, f"mux({sel})")

def get_visual_edges(node):
    if isinstance(node, IfStatement):
        return [
            ("cond", node.cond),
            ("then", node.then_branch),
            ("else", node.else_branch),
        ]
    elif isinstance(node, LogicMux):
        return [
            ("selector", node.selector),
            ("if_true", node.if_true),
            ("if_false", node.if_false),
        ]
    elif isinstance(node, CaseStatement):
        edges = [("selector", node.selector)]
        for (case_expr, branch) in node.case_items:
            label = case_expr.label() if hasattr(case_expr, "label") else str(case_expr)
            edges.append((label, branch))
        if node.default_branch:
            edges.append(("default", node.default_branch))
        return edges

    if isinstance(node, EmptyBranch):
        return "(empty)", {"style": "filled", "fillcolor": "#eeeeee", "fontcolor": "#888888"}
    elif hasattr(node, "inputs"):
        return [(None, child) for child in node.inputs()]
    elif hasattr(node, "children"):
        return [(None, child) for child in node.children]
    return []

def get_visual_attributes(node):
    """Returns shape, fillcolor, tooltip, and optional href for visualization."""
    structural_styles = {
        IfStatement:     ("diamond",    "lightyellow", "Conditional IfStatement"),
        CaseStatement:   ("diamond",    "lightcoral",  "Multi-way CaseStatement"),
        LogicAssign:     ("hexagon",    "lightskyblue", "Assignment"),
    }

    default_shape = "box"
    default_color = "lightgray"
    default_tooltip = node.__class__.__name__

    for cls, (shape, color, tooltip) in structural_styles.items():
        if isinstance(node, cls):
            return shape, color, tooltip, None  # No hyperlink yet

    # Fallback for logic ops or leaves
    return default_shape, default_color, default_tooltip, None
