import json
from logictree.utils.serialize import logic_tree_to_json
from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.ops import AndOp, OrOp

tree = AndOp(
       LogicVar("a"),
       OrOp(LogicVar("b"), LogicConst(1))
)

from logictree.transforms.simplify import simplify_logic_tree
simplified = simplify_logic_tree(tree)
print("LogicTree:")
print(str(tree))
print("Simplified Tree:")
print(str(simplified))


#for k, v in result.items():
#    print(f"{k}: {v} ({type(v)})")

result = logic_tree_to_json(simplified)
print("JSON:")
print(json.dumps(result, indent=2))

#print(json.dumps(logic_tree_to_json(tree), indent=2))

