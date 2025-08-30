import os
import subprocess
from typing import Optional

from logictree.utils.paths import OUTPUT_DIR
from logictree.utils.graphviz_export import logic_tree_to_dot


def _run_dot(dot_path: str, fmt: str = "png", output_path: Optional[str] = None):
    """
    Internal helper to convert .dot file to the specified format using Graphviz.

    Args:
        dot_path: Path to .dot file.
        out_format: Format to convert to (e.g., 'svg', 'png').

    Returns:
        Path to generated output file.
    """
    if not os.path.exists(dot_path):
        raise FileNotFoundError(f"{dot_path} does not exist")

    if output_path is None:
        output_path = dot_path.replace(".dot", f".{fmt}")

    if fmt not in ("svg", "png"):
        raise ValueError(f"Unsupported output format: {fmt}")

    try:
        print(f"DEBUG: _run_dot() dot -T{fmt} {dot_path} -o {output_path}")
        cmd = ["dot", f"-T{fmt}", dot_path, "-o", output_path]
        subprocess.run(cmd, check=True)

        return output_path
    except FileNotFoundError:
        raise RuntimeError("Graphviz 'dot' command not found. Is Graphviz installed?")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Graphviz failed: {e}")


def to_svg(tree, name="logic_tree") -> str:
    dot = logic_tree_to_dot(tree)
    dot_path = os.path.join(OUTPUT_DIR, f"output_sig_{name}.dot")
    with open(dot_path, "w") as f:
        f.write(dot.source if hasattr(dot, "source") else str(dot))
    print(f"[DEBUG] Writing DOT file to {dot_path}")
    return _run_dot(dot_path, "svg")


def to_png(tree, name="logic_tree") -> str:
    dot = logic_tree_to_dot(tree)
    dot_path = os.path.join(OUTPUT_DIR, f"output_sig_{name}.dot")
    with open(dot_path, "w") as f:
        f.write(dot.source if hasattr(dot, "source") else str(dot))
    print(f"[DEBUG] Writing DOT file to {dot_path}")
    return _run_dot(dot_path, "png")
