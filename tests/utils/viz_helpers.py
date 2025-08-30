# tests/utils/viz_helpers.py
from pathlib import Path

from logictree.utils.output import render_png


def assert_viz(node, name="circuit", out_dir="./output"):
    png_path = render_png(node, out_dir=out_dir, name=name)
    assert Path(png_path).exists(), f"PNG not generated: {png_path}"
    return png_path
