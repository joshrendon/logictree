import pytest

pytestmark = [pytest.mark.unit]

import json

from logictree.nodes.ops import AndOp, OrOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.utils.serialize import logic_tree_to_json

tree = AndOp(
       LogicVar("a"),
       OrOp(LogicVar("b"), LogicConst(1))
)

from logictree.transforms.simplify import simplify_logic_tree

simplified = simplify_logic_tree(tree)
print("LogicTree:")
print(tree)
print("Simplified Tree:")
print(simplified)

result = logic_tree_to_json(simplified)
print("JSON:")
print(json.dumps(result, indent=2))
