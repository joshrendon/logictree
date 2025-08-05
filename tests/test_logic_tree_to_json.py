import json
from logictree.utils.serialize import logic_tree_to_json
from logictree.nodes.ops.ops import LogicVar, LogicConst, LogicOp

tree = LogicOp("AND", [
    LogicVar("a"),
    LogicOp("OR", [LogicVar("b"), LogicConst(1)])
])

simplified = tree.simplify()
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

