from pathlib import Path


def find_repo_root(markers=("pyproject.toml", ".git")) -> Path:
    """Walk upwards until a repo root marker is found."""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if any((parent / m).exists() for m in markers):
            return parent
    raise RuntimeError("Repo root not found")


# Canonical repo root + output dir
REPO_ROOT = find_repo_root()
OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
