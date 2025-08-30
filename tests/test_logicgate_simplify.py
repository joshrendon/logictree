import pytest

pytestmark = [pytest.mark.unit]

from logictree.nodes.ops.ops import LogicTreeNode
from logictree.transforms.simplify import simplify
from tests.utils import EXCLUDED_CLASSES, all_subclasses, safe_instantiate


def test_all_gates_implement_simplify():
    bad_simplify = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue
        instance = safe_instantiate(cls)
        if instance is None:
            continue
        try:
            _ = simplify(instance)
        except Exception:
            bad_simplify.append(cls.__name__)

    assert not bad_simplify, f"Failed simplify() on: {', '.join(bad_simplify)}"
