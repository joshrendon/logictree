import inspect

import pytest

from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect


def all_subclasses(cls):
    """Recursively collect all subclasses of a class."""
    subclasses = set(cls.__subclasses__())
    for sub in list(subclasses):
        subclasses |= all_subclasses(sub)
    return subclasses


@pytest.mark.unit
@pytest.mark.parametrize("node_cls", list(all_subclasses(LogicTreeNode)))
def test_node_init_autocheck(node_cls):
    """
    Smoke test: ensure each LogicTreeNode subclass can be instantiated
    with dummy arguments without raising exceptions.
    """

    # Skip abstract base classes (like LogicOp)
    if inspect.isabstract(node_cls) or node_cls.__name__ == "LogicOp":
        pytest.skip(f"{node_cls.__name__} is abstract, skipping")

    sig = inspect.signature(node_cls.__init__)
    kwargs = {}

    for name, param in sig.parameters.items():
        if name == "self":
            continue

        # heuristic dummy values by arg name
        if "name" in name:
            kwargs[name] = "x"
        elif "var" in name or "lhs" in name or "rhs" in name:
            kwargs[name] = LogicVar("dummy")
        elif "value" in name:
            kwargs[name] = True
        elif "children" in name:
            kwargs[name] = [LogicVar("a")]
        elif "cases" in name:
            kwargs[name] = {0: LogicVar("a")}
        elif "default" in name:
            kwargs[name] = LogicVar("b")
        elif "labels" in name:
            kwargs[name] = [LogicConst("default")]
        elif name == "op":
            kwargs[name] = "and"
        elif "inputs" in name or "args" in name:
            kwargs[name] = [LogicVar("a"), LogicVar("b")]
        elif "selector" in name or "condition" in name:
            kwargs[name] = LogicVar("sel")
        elif "then" in name or "else" in name or "branch" in name:
            kwargs[name] = LogicVar("branch")
        else:
            # fallback None
            kwargs[name] = None

    # Only keep kwargs that are actually in the signature
    valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    node = node_cls(**valid_kwargs)
    assert isinstance(node, node_cls)


@pytest.mark.unit
@pytest.mark.parametrize("node", [
    BitSelect(LogicVar("s"), 0),
    PartSelect(LogicVar("s"), 7, 4),
    Concat([LogicVar("a"), LogicConst(1)])
])
def test_selects_nodes_init(node):
    """Smoke test: ensure BitSelect, PartSelect, and Concat construct cleanly."""
    assert node is not None
    assert "s" in repr(node) or "a" in repr(node)
