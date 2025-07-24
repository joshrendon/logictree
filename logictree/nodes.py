from typing import List, Union
from .graphviz_utils import to_svg, to_png
import itertools
GATE_TYPES = ['AND', 'OR', 'NOT', 'XNOR', 'MUX']

class LogicNode:
    def depth(self):
        raise NotImplementedError

    def inputs(self) -> set[str]:
        return self.collect_input_names()
        #raise NotImplementedError

    def to_verilog(self):
        raise NotImplementedError

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError

    def contains_hole(self):
        return False
    
    def collect_input_names(self) -> set["LogicVar"]:
        return NotImplementedError("Subclasses should implement collect_inputs")


class LogicVar(LogicNode):
    def __init__(self, name):
        self.name = name

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


class LogicConst(LogicNode):
    def __init__(self, value):
        self.value = value

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


class LogicHole(LogicNode):
    def __init__(self, name="UNSPECIFIED"):
        self.name = name

    def inputs(self) -> set[str]:
        return self.collect_input_names()

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

    def collect_input_names(self) -> set[str]:
        return {self.name}


class LogicOp(LogicNode):
    def __init__(self, op, inputs):
        assert op in GATE_TYPES
        assert isinstance(op, str)
        self.name = op
        self.op = op
        self.children = [
                inp if isinstance(inp, LogicNode) else LogicHole(f"input_{i}")
                for i, inp in enumerate(inputs)
        ]

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

class NotOp(LogicOp):
    def __init__(self, child):
        super().__init__('NOT', [child])

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

