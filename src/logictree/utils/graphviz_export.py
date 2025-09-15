# logictree.utils/graphviz_export.py
import subprocess
from pathlib import Path

from .visual import get_visual_edges


def logic_tree_to_dot(logic_tree, signal_name="logic", gate_colors=None):
    """Generate a Graphviz .dot string from a LogicTree structure."""
    if gate_colors is None:
        gate_colors = {
            "AND": "lightblue",
            "OR": "lightgreen",
            "NOT": "orange",
            "XNOR": "plum",
            "XOR": "yellow",
            "NAND": "red",
            "NOR": "purple",
        }

    lines = [f'digraph "{signal_name}_tree" {{']
    lines.append('rankdir="BT";')
    lines.append('  node [style=filled, shape=box, fontname="Courier"];')

    node_id = 0
    id_map = {}

    def visit(node):
        nonlocal node_id
        if node in id_map:
            return id_map[node]
    
        curr_id = f"n{node_id}"
        id_map[node] = curr_id
        node_id += 1
    
        # Set label and color
        if hasattr(node, "name"):
            label = node.name
            color = gate_colors.get(label, "gray")
        elif hasattr(node, "value"):
            label = str(node.value)
            color = "white"
        else:
            label = str(node)
            color = "lightgray"
    
        lines.append(f'  {curr_id} [label="{label}", fillcolor="{color}"];')
    
        # NEW: Get visual attributes
        from logictree.utils.visual import get_visual_attributes  # Add this import at top of file
        
        label = node.label() if hasattr(node, "label") else str(node)
        shape, color, tooltip, href = get_visual_attributes(node)
        
        # Build DOT node string
        node_line = f'  {curr_id} [label="{label}", fillcolor="{color}", shape="{shape}", tooltip="{tooltip}"'
        if href:
            node_line += f', href="{href}"'
        node_line += "];"
        lines.append(node_line)

        for label, child in get_visual_edges(node):
            if child is not None:
                child_id = visit(child)
                if label:
                    lines.append(f'  {child_id} -> {curr_id} [label="{label}"];')
                else:
                    lines.append(f"  {child_id} -> {curr_id};")

        return curr_id
    visit(logic_tree)
    lines.append("}")
    return "\n".join(lines)


def save_dot_svg_png(dot_str, basename):
    """Save .dot and generate .svg and .png using Graphviz 'dot'."""
    base = Path(basename)
    dot_file = base.with_suffix(".dot")
    svg_file = base.with_suffix(".svg")
    png_file = base.with_suffix(".png")

    print("[DEBUG] saving svg and png files")
    dot_file.write_text(dot_str)
    subprocess.run(["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)], check=True)
    subprocess.run(["dot", "-Tpng", str(dot_file), "-o", str(png_file)], check=True)

    return dot_file, svg_file, png_file
