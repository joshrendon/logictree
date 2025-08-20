# tests/conftest.py
import sys
from pathlib import Path

# Add the repo root (one level up from /tests) to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
