import json
from logictree.utils.serialize import logic_tree_to_json
from logictree.nodes.ops.ops import LogicVar, LogicConst, LogicOp
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.control.assign import LogicAssign

selector = LogicVar("s")

assign0 = LogicAssign("out", LogicVar("a"))
assign1 = LogicAssign("out", LogicVar("b"))

# Case items
case_item0 = CaseItem(labels=[0], body=assign0)
case_item1 = CaseItem(labels=[1], body=assign1)
print("Case item 0:", case_item0.labels)
print("Case item 1:", case_item1.labels)

# Top level case statement
case_stmt = CaseStatement(selector=selector, items=[case_item0, case_item1])

# Clone and simplify
cloned = case_stmt.clone()
print("CLONED item 0 labels:", cloned.items[0].labels)
print("CLONED item 1 labels:", cloned.items[1].labels)

simplified = cloned.simplify()

print("Original Tree:")
print(case_stmt)
print("\nSimplified Tree:")
print(simplified)

assert isinstance(simplified, IfStatement)
# Type check
assert type(simplified).__name__ != "CaseStatement", "CaseStatement was not simplified"

