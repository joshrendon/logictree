from typing import List, Union
from .graphviz_utils import to_svg, to_png
import itertools
GATE_TYPES = ['AND', 'OR', 'NOT', 'XNOR']

class LogicNode:
    def depth(self):
        raise NotImplementedError

    def to_verilog(self):
        raise NotImplementedError

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError

    def contains_hole(self):
        return False


class LogicVar(LogicNode):
    def __init__(self, name):
        self.name = name

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


class LogicConst(LogicNode):
    def __init__(self, value):
        self.value = value

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


class LogicHole(LogicNode):
    def __init__(self, name="UNSPECIFIED"):
        self.name = name

    def depth(self):
        return 0

    def to_verilog(self):
        return f"/* {self.name} */"

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="Hole\\n{self.name}", shape=octagon, style=dashed];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def contains_hole(self):
        return True

    def __repr__(self):
        return f"LogicHole({self.name})"


class LogicOp(LogicNode):
    def __init__(self, op, inputs):
        assert op in GATE_TYPES
        self.name = op
        self.inputs = [
                inp if isinstance(inp, LogicNode) else LogicHole(f"input_{i}")
                for i, inp in enumerate(inputs)
        ]

    def depth(self):
        return 1 + max(inp.depth() for inp in self.inputs)

    def to_verilog(self):
        if self.name == "NOT":
            print(f"DEBUG: LogicOp::to_verilog() self.inputs[0]:{self.inputs[0]}, name: {self.name}")
            return f"~({self.inputs[0].to_verilog()})"
        return f"({self.inputs[0].to_verilog()} {self.name} {self.inputs[1].to_verilog()})"

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="{self.name}", shape=circle];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        for inp in self.inputs:
            inp.to_dot(graph, my_id, next_id)
        return my_id

    def contains_hole(self):
        return any(inp.contains_hole() for inp in self.inputs)

    def __repr__(self):
        return f"LogicOp({self.name}, {self.inputs})"


# Utility API
def repair_tree_inputs(node):
    if isinstance(node, LogicOp):
        for i, inp in enumerate(node.inputs):
            if inp is None:
                print(f"[repair] Inserting LogicHole at input {i} of {node.name}")
                node.inputs[i] = LogicHole(f"missing_input_{i}")
            else:
                repair_tree_inputs(inp)

def count_gate_type(tree, gate_name):
    if isinstance(tree, LogicOp):
        return int(tree.name == gate_name) + sum(count_gate_type(inp, gate_name) for inp in tree.inputs)
    elif isinstance(tree, LogicNode):
        return 0
    return 0


def gate_count(tree):
    return {g: count_gate_type(tree, g) for g in GATE_TYPES}


def gate_summary(tree):
    counts = gate_count(tree)
    return ", ".join(f"{k}:{v}" for k, v in counts.items() if v > 0)

