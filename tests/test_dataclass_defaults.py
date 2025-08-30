# tests/test_dataclass_defaults.py

import dataclasses
import importlib
import inspect
import pkgutil

import pytest

import logictree.nodes as nodes_pkg


def iter_node_classes():
    """Recursively yield all classes defined in logictree.nodes submodules."""
    pkgpath = nodes_pkg.__path__  # type: ignore[attr-defined]
    prefix = nodes_pkg.__name__ + "."

    for _, modname, ispkg in pkgutil.walk_packages(pkgpath, prefix):
        module = importlib.import_module(modname)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__.startswith(prefix):
                yield obj


def is_dataclass_type(cls):
    return dataclasses.is_dataclass(cls)


@pytest.mark.parametrize("cls", list(iter_node_classes()))
def test_dataclass_default_factories(cls):
    """Ensure dataclasses never use bare mutable defaults (Field objects)."""
    if not is_dataclass_type(cls):
        pytest.skip(f"{cls.__name__} is not a dataclass")

    for field in dataclasses.fields(cls):
        default = field.default
        default_factory = field.default_factory

        # If the default is a dataclasses.Field, something's wrong
        assert not isinstance(default, dataclasses.Field), (
            f"{cls.__module__}.{cls.__name__}.{field.name} "
            f"uses 'field(default=...)' incorrectly"
        )

        # Flag common mutable defaults
        if default not in (dataclasses.MISSING, None):
            if isinstance(default, (dict, list, set)):
                pytest.fail(
                    f"{cls.__module__}.{cls.__name__}.{field.name} "
                    f"has mutable default {type(default).__name__}; "
                    f"use default_factory instead"
                )
