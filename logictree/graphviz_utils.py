import os
import subprocess

def _run_dot(dot_path: str, out_format: str) -> str:
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

    if out_format not in ('svg', 'png'):
        raise ValueError(f"Unsupported output format: {out_format}")

    out_path = dot_path.replace(".dot", f".{out_format}")
    try:
        subprocess.run(
            ["dot", f"-T{out_format}", dot_path, "-o", out_path],
            check=True
        )
        return out_path
    except FileNotFoundError:
        raise RuntimeError("Graphviz 'dot' command not found. Is Graphviz installed?")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Graphviz failed: {e}")

def to_svg(dot_path: str) -> str:
    return _run_dot(dot_path, "svg")

def to_png(dot_path: str) -> str:
    return _run_dot(dot_path, "png")

