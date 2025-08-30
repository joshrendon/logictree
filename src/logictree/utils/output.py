import json
import subprocess
from pathlib import Path

from logictree.utils.display import to_dot
from logictree.utils.serialize import logic_tree_to_json


def write_dot_to_file(node, filepath: str | Path):
    dot_str = to_dot(node)
    filepath = Path(filepath)
    filepath.write_text(dot_str.source)
    return filepath


def render_png(node, out_dir="./output", name="circuit"):
    """Render a LogicTreeNode (or LogicAssign) to DOT + PNG in ./output/"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dot_path = out_dir / f"{name}.dot"
    png_path = out_dir / f"{name}.png"

    # Write DOT
    write_dot_to_file(node, dot_path)

    # Convert to PNG with Graphviz
    subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
    return png_path


def write_png(node, filepath):
    dot = to_dot(node)
    dot.render(str(filepath), format="png", cleanup=True)


def write_json_to_file(node, filepath):

    if hasattr(node, "to_ir_dict"):
        data = node.to_ir_dict()
    else:
        data = logic_tree_to_json(node)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
