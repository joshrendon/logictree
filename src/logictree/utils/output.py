import json
import subprocess
from pathlib import Path
import graphviz

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicVar, LogicConst, LogicOp
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp
from logictree.utils.display import pretty_print
from logictree.utils.display import to_dot
from logictree.utils.serialize import logic_tree_to_json


def write_dot_to_file(node, filepath: str | Path):
    dot_str = to_dot(node)
    filepath = Path(filepath)
    filepath.write_text(dot_str.source)
    return filepath

def render_png_multi(nodes, out_dir="./output", name="circuit", edge_style="spline") -> str:
    """
    Render multiple LogicTree nodes (e.g., bit-vector primitives)
    into a single PNG side by side.
    """
    out_path = Path(out_dir) / f"{name}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="TB") # flip so root is at the top
    dot.attr(splines=edge_style)
    #dot.attr(splines="ortho") # straighter lines
    dot.attr(nodesep="0.4", ranksep="0.6")

    for i, node in enumerate(nodes):
        cache = {}
        with dot.subgraph(name=f"cluster_bit{i}") as sg:
            sg.attr(label=f"y[{i}]", color="blue")
            _render_node(sg, node, cache, suffix=f"_b{i}")

    dot.render(out_path.with_suffix(""), cleanup=True)
    return str(out_path)

def _render_node(dot: graphviz.Digraph, node: LogicTreeNode, cache: dict, suffix: str) -> str:
    """
    Render a node with a short label and edges for each child.
    """
    key = (id(node), suffix)
    if key in cache:
        return cache[key]

    node_id = f"n{len(cache)}{suffix}"
    cache[key] = node_id

    # --- Label & style
    if isinstance(node, LogicVar):
        label, shape, fill = node.name, "ellipse", "#7FB3FF"
    elif isinstance(node, LogicConst):
        label, shape, fill = str(node.value), "ellipse", "#BFBFBF"
    elif isinstance(node, AndOp):
        label, shape, fill = "AND", "box", "#8EE085"
    elif isinstance(node, OrOp):
        label, shape, fill = "OR", "box", "#F7A84B"
    elif isinstance(node, NotOp):
        label, shape, fill = "NOT", "box", "#F26363"
    else:
        label, shape, fill = type(node).__name__, "box", "#DDDDDD"

    dot.node(node_id, label=label, shape=shape, style="filled", fillcolor=fill)

    # --- Edges to children
    for child in getattr(node, "children", []):
        cid = _render_node(dot, child, cache, suffix)
        #dot.edge(cid, node_id)
        dot.edge(node_id, cid)

    return node_id

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
