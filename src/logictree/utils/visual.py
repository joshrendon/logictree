# logictree/utils/visual.py
from .overlay import set_label


def annotate_mux_node(node):
    sel = node.selector.label() if hasattr(node, "selector") else "?"
    set_label(node, f"mux({sel})")
