# tests/utils/viz_helpers.py
from pathlib import Path

from logictree.utils.output import render_png


#def assert_viz(node, name="circuit", out_dir="./output"):
#    png_path = render_png(node, out_dir=out_dir, name=name)
#    assert Path(png_path).exists(), f"PNG not generated: {png_path}"
#    return png_path

def assert_viz(node_or_nodes, name="circuit", out_dir="./output"):
    """
    Assert that a LogicTree node or list of nodes can be rendered to PNG.

    - If a single node is given, render as usual.
    - If a list of nodes is given (multi-bit output), render each bit
      to its own PNG with indexed suffix: <name>_bit<i>.png
    """
    if isinstance(node_or_nodes, list):
        png_paths = []
        for i, bitnode in enumerate(node_or_nodes):
            bit_name = f"{name}_bit{i}"
            png_path = render_png(bitnode, out_dir=out_dir, name=bit_name)
            assert Path(png_path).exists(), f"PNG not generated: {png_path}"
            png_paths.append(png_path)
        return png_paths
    else:
        png_path = render_png(node_or_nodes, out_dir=out_dir, name=name)
        assert Path(png_path).exists(), f"PNG not generated: {png_path}"
        return png_path
#def assert_viz(tree, name: str="circuit", outdir="./output"):
#    """
#    Render a Graphviz visualization of a LogicTree node or list of nodes.
#    Returns the path to the generated PNG.
#    """
#    outdir = Path(outdir)
#    outdir.mkdir(parents=True, exist_ok=True)
#
#    if isinstance(tree, list):
#        # Multi-bit: generate one figure with all bits stacked
#        from graphviz import Digraph
#        dot = Digraph(comment=f"{name}_multi")
#        for i, t in enumerate(tree):
#            subname = f"{name}_bit{i}"
#            subdot = t.to_graphviz(name=subname)
#            dot.subgraph(subdot)   # keep them in same figure
#        out_path = outdir / f"{name}.png"
#        dot.render(out_path.with_suffix(""), format="png", cleanup=True)
#        return out_path
#
#    else:
#        out_path = outdir / f"{name}.png"
#        dot = tree.to_graphviz(name)
#        dot.render(out_path.with_suffix(""), format="png", cleanup=True)
#        return out_path
