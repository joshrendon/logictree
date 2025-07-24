# utils/graphviz_export.py

from pathlib import Path
import subprocess

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
            "NOR": "purple"
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

        if hasattr(node, 'name'):
            label = node.name
            color = gate_colors.get(label, "gray")
        elif hasattr(node, 'value'):
            label = str(node.value)
            color = "white"
        else:
            label = str(node)
            color = "lightgray"

        lines.append(f'  {curr_id} [label="{label}", fillcolor="{color}"];')

        if hasattr(node, 'inputs'):
            for child in node.inputs:
                if child is not None:
                    child_id = visit(child)
                    lines.append(f"  {child_id} -> {curr_id};")
        elif hasattr(node, 'children'):
            for child in node.children:
                if child is not None:
                    child_id = visit(child)
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

