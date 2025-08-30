# logictree/nodes/ops/__init__.py
"""
Ops package: logical primitives and gates.
Dynamic runtime loader + static re-exports for type checkers.
"""
import importlib
import pkgutil

__all__ = []

# Import ops.py explicitly first
_ops = importlib.import_module(f"{__name__}.ops")
if hasattr(_ops, "__all__"):
    for _name in _ops.__all__:
        globals()[_name] = getattr(_ops, _name)
    __all__.extend(_ops.__all__)

# Import all other submodules (like gates, comparison, etc.)
for _loader, _modname, _is_pkg in pkgutil.iter_modules(__path__):
    if _modname == "ops":
        continue
    _mod = importlib.import_module(f"{__name__}.{_modname}")
    if hasattr(_mod, "__all__"):
        for _name in _mod.__all__:
            globals()[_name] = getattr(_mod, _name)
        __all__.extend(_mod.__all__)


# --- Explicit re-exports for static type checkers (mypy, pyright) ---
from .comparison import EqOp, NeqOp
from .gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from .mux import LogicMux
from .ops import LogicConst, LogicOp, LogicVar

__all__ += [
    "LogicConst",
    "LogicVar",
    "LogicOp",
    "AndOp",
    "OrOp",
    "NotOp",
    "XorOp",
    "NandOp",
    "NorOp",
    "XnorOp",
    "EqOp",
    "NeqOp",
    "LogicMux",
]
