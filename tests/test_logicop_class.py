import pytest

pytestmark = [pytest.mark.unit]

from logictree.nodes.ops.ops import LogicTreeNode
from tests.utils_bitselect import EXCLUDED_CLASSES, all_subclasses, safe_instantiate


def test_all_gates_implement_operands():
    bad_classes = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            _ = instance.operands
        except NotImplementedError:
            bad_classes.append(cls.__name__)
        except Exception:
            bad_classes.append(f"{cls.__name__} (bad .operands impl?)")

    assert not bad_classes, f"Missing or bad `.operands` in: {', '.join(bad_classes)}"

def test_all_gates_implement_label():
    bad_classes = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            label = instance.label()
            assert isinstance(label, str)
        except Exception:
            bad_classes.append(cls.__name__)

    assert not bad_classes, f"Missing or bad `.label()` in: {', '.join(bad_classes)}"

def test_all_gates_implement_children():
    bad_classes = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            children = instance.children
            assert isinstance(children, (list, tuple))
        except Exception:
            bad_classes.append(cls.__name__)

    assert not bad_classes, f"Missing or bad `.children` in: {', '.join(bad_classes)}"

def test_all_gates_implement_to_json_dict():
    bad_classes = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            d = instance.to_json_dict()
            assert isinstance(d, dict)
        except Exception:
            bad_classes.append(cls.__name__)

    assert not bad_classes, f"Missing or bad `.to_json_dict()` in: {', '.join(bad_classes)}"

def test_all_gates_implement_depth_and_delay():
    bad_depth = []
    bad_delay = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            d = instance.depth
            assert isinstance(d, int)
        except Exception:
            bad_depth.append(cls.__name__)

        try:
            t = instance.delay
            assert isinstance(t, int)
        except Exception:
            bad_delay.append(cls.__name__)

    assert not bad_depth, f"Missing or bad `.depth()` in: {', '.join(bad_depth)}"
    assert not bad_delay, f"Missing or bad `.delay()` in: {', '.join(bad_delay)}"


subclasses = sorted(
    (cls for cls in all_subclasses(LogicTreeNode) if cls.__name__ not in EXCLUDED_CLASSES),
    key=lambda c: c.__name__,
)

@pytest.mark.parametrize("cls", subclasses, ids=lambda c: c.__name__)
def test_label_method(cls):
    instance = safe_instantiate(cls)
    assert instance is not None, f"Failed to instantiate {cls.__name__}"
    label = instance.label()
    assert isinstance(label, str), f"{cls.__name__}.label() did not return a string"


# Properties like these are NOT callable
PROPERTY_METHODS = {"depth", "delay"}

@pytest.mark.parametrize("method_name", sorted(["label", "depth", "delay", "to_json_dict"]))
@pytest.mark.parametrize("cls", subclasses, ids=lambda c: c.__name__)
def test_method_implementation(cls, method_name):
    instance = safe_instantiate(cls)
    assert instance is not None, f"Could not instantiate {cls.__name__}"
    
    attr = getattr(instance, method_name, None)
    assert attr is not None, f"{cls.__name__} is missing `{method_name}`"

    if method_name in PROPERTY_METHODS:
        try:
            val = attr  # Don't call it
            assert val is not None or val == 0
        except Exception as e:
            pytest.fail(f"{cls.__name__}.{method_name} raised: {e}")
    else:
        assert callable(attr), f"{cls.__name__}.{method_name} is not callable"
