import pytest

pytestmark = [pytest.mark.integration]
import logging

from logictree.analysis.delay import delay
from logictree.nodes.ops.ops import LogicOp
from logictree.nodes.registry import all_node_classes
from logictree.nodes.struct.module import Module
from tests.utils_bitselect import safe_instantiate

log = logging.getLogger(__name__)


def test_all_nodes_delay_returns_number():
    failed = []

    for cls in all_node_classes():
        if cls in (LogicOp, Module):
            continue

        try:
            node = safe_instantiate(cls)
            if node is None:
                continue

            try:
                val = delay(node)
                assert isinstance(val, (int, float)), \
                f"{cls.__name__}.delay returned {type(val)}"
            except Exception as e:
                failed.append(f"{cls.__name__}.delay raised: {repr(e)}")

        except Exception as e:
            failed.append(f"{cls.__name__} instantiation failed {repr(e)}")

    assert not failed, "\n".join(failed)
