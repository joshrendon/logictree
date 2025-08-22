# logictree/nodes/ops/__init__.py
import importlib
import pkgutil

__all__ = []

# Import ops.py explicitly first
_ops = importlib.import_module(f"{__name__}.ops")
if hasattr(_ops, "__all__"):
    for _name in _ops.__all__:
        globals()[_name] = getattr(_ops, _name)
    __all__.extend(_ops.__all__)

# Now import every other submodule (e.g., gates.py)
for _loader, _modname, _is_pkg in pkgutil.iter_modules(__path__):
    if _modname == "ops":
        continue
    _mod = importlib.import_module(f"{__name__}.{_modname}")
    if hasattr(_mod, "__all__"):
        for _name in _mod.__all__:
            globals()[_name] = getattr(_mod, _name)
        __all__.extend(_mod.__all__)
