import pytest
import inspect
from logictree.nodes.ops.ops import LogicTreeNode, LogicVar
from tests.utils import EXCLUDED_CLASSES
pytestmark = [pytest.mark.unit]

def test_all_gates_implement_operands():
    """
    Ensure every LogicTreeNode subclass that *should* implement `.operands`
    actually does, and is instantiable with dummy LogicVar args.
    """

    def all_subclasses(cls):
        subclasses = set()
        work = [cls]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
        return subclasses

    bad_classes = []

    for cls in all_subclasses(LogicTreeNode):
        if cls.__name__ in EXCLUDED_CLASSES:
            continue

        try:
            sig = inspect.signature(cls.__init__)
        except Exception:
            continue  # skip builtins or funky classes

        # Get all positional params (excluding self)
        params = list(sig.parameters.values())[1:]

        # Skip if no required params
        if not params:
            continue

        try:
            # Build dummy args
            dummy_args = []
            dummy_kwargs = {}
            for i, p in enumerate(params):
                if p.default != inspect.Parameter.empty:
                    continue  # skip optional
                if p.kind == inspect.Parameter.KEYWORD_ONLY:
                    dummy_kwargs[p.name] = LogicVar(name=f"x{i}")
                else:
                    dummy_args.append(LogicVar(name=f"x{i}"))

            instance = cls(*dummy_args, **dummy_kwargs)
            _ = instance.operands
        except NotImplementedError:
            bad_classes.append(cls.__name__)
        except Exception as e:
            bad_classes.append(f"{cls.__name__} (bad init: {e})")

    assert not bad_classes, f"Missing .operands or bad init in: {', '.join(bad_classes)}"
