"""
Logictree debug utility module
"""

from dataclasses import Field


def assert_no_fields(obj, name="root"):
    """
    Recursively check that no attributes in a LogicTreeNode tree are uninitialized dataclass.Field objects.
    """
    if isinstance(obj, Field):
        raise TypeError(f"{name} is a dataclasses.Field object — likely uninitialized")

    if hasattr(obj, "__dict__"):  # typical for dataclass or class instances
        for attr_name, attr_value in vars(obj).items():
            assert_no_fields(attr_value, f"{name}.{attr_name}")

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_no_fields(item, f"{name}[{i}]")

    elif isinstance(obj, dict):
        for k, v in obj.items():
            assert_no_fields(v, f"{name}[{k}]")
