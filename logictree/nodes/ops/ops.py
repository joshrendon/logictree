from logictree.nodes.base import LogicTreeNode
from typing import List, Union
from logictree.utils.display import indent
from logictree.nodes.types import GATE_TYPES

class LogicConst(LogicTreeNode):
    def __init__(self, value):
        self.value = value

    def simplify(self):
        return self

    def __str__(self):
        return str(self.value)

    #def __str__(self):
    #    return "True" if self.value == 1 else "False"

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    def depth(self):
        return 0

    def to_verilog(self):
        return self.value

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.value}", shape=box];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def __repr__(self):
        return f"LogicConst({self.value})"

    def collect_input_names(self) -> set[str]:
        return set()


class LogicVar(LogicTreeNode):
    def __init__(self, name):
        self.name = name

    def simplify(self):
        return self

    def __str__(self):
        return self.name

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    def depth(self):
        return 0

    def to_verilog(self):
        return self.name

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.name}", shape=ellipse];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def __repr__(self):
        return f"LogicVar({self.name})"

    def collect_input_names(self) -> set[str]:
        return {self.name}


class LogicOp(LogicTreeNode):
    def __init__(self, op, inputs):
        assert op in GATE_TYPES
        assert isinstance(op, str)
        self.name = op
        self.op = op
        self.children = [
                inp if isinstance(inp, LogicTreeNode) else LogicHole(f"input_{i}")
                for i, inp in enumerate(inputs)
        ]

    def simplify(self):
        simplified_ops = [op.simplify() for op in self.inputs]
        # Simple constant folding example
        if self.op == 'AND':
            if any(isinstance(op, LogicConst) and op.value == 0 for op in simplified_ops):
                return LogicConst(0)
            simplified_ops = [op for op in simplified_ops if not (isinstance(op, LogicConst) and op.value == 1)]
        return LogicOp(self.op, simplified_ops)

    def __str__(self):
        return f"({f' {self.op} '.join(map(str, self.inputs()))})"

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    def depth(self):
        return 1 + max(inp.depth() for inp in self.children)

    def to_verilog(self):
        if self.name == "NOT":
            print(f"DEBUG: LogicOp::to_verilog() self.children[0]:{self.children[0]}, name: {self.name}")
            return f"~({self.children[0].to_verilog()})"
        return f"({self.children[0].to_verilog()} {self.name} {self.children[1].to_verilog()})"

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.name}", shape=circle];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        for inp in self.children:
            inp.to_dot(graph, my_id, next_id)
        return my_id

    def contains_hole(self):
        return any(inp.contains_hole() for inp in self.children)

    def __repr__(self):
        return f"LogicOp({self.name}, {self.children})"

    def collect_input_names(self) -> set[str]:
        names = set()
        for c in self.children:
            names.update(c.collect_input_names())
        return names

