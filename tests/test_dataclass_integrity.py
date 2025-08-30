# tests/test_dataclass_integrity.py
import dataclasses
import importlib
import inspect
import pkgutil

import pytest

import logictree


def iter_logictree_modules():
    """Yield all submodules in the logictree package."""
    for mod in pkgutil.walk_packages(
        logictree.__path__, logictree.__name__ + "."
    ):
        yield mod.name


@pytest.mark.parametrize("modname", list(iter_logictree_modules()))
def test_import_module(modname):
    """Make sure every logictree module imports cleanly."""
    importlib.import_module(modname)


def dataclass_classes():
    """Find every dataclass class in logictree.*"""
    for modname in iter_logictree_modules():
        mod = importlib.import_module(modname)
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if dataclasses.is_dataclass(obj):
                yield f"{modname}.{name}", obj


@pytest.mark.parametrize("clsinfo", list(dataclass_classes()))
def test_dataclass_instantiation(clsinfo):
    """Try instantiating dataclasses with no args to check defaults."""
    fqname, cls = clsinfo
    try:
        instance = cls()  # may fail if required args
    except TypeError:
        pytest.skip(f"{fqname} requires args")
        return

    # Walk fields and assert no dataclasses.Field leaked
    for f in dataclasses.fields(cls):
        val = getattr(instance, f.name)
        assert not isinstance(val, dataclasses.Field), (
            f"{fqname}.{f.name} defaulted to a dataclasses.Field!"
        )
