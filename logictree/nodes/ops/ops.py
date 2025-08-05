from logictree.nodes.base import LogicTreeNode
from typing import List, Union
from logictree.utils.display import indent
from logictree.nodes.types import GATE_TYPES, COMMUTATIVE_OPS
import logging
log = logging.getLogger(__name__)

class LogicConst(LogicTreeNode):
    def __init__(self, value):
        super().__init__()
        self.value = value

    @property
    def delay(self):
        return 0

    @property
    def expr_source(self):
        return None

    def default_label(self):
        return str(self.value)

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            "expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }

    @property
    def children(self):
        return  []
    
    def equals(self, other):
        return isinstance(other, LogicConst) and self.value == other.value

    def simplify(self):
        return self

    def __str__(self):
        return str(self.value)

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    @property
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
        super().__init__()
        self.name = name

    @property
    def expr_source(self):
        return None

    @property
    def delay(self):
        return 0

    #def label(self):
    #    return self.name

    def default_label(self):
        return self.name

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            "expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }
        
    @property
    def children(self):
        return  []

    def equals(self, other):
        return isinstance(other, LogicVar) and self.name == other.name

    def simplify(self):
        return self

    def __str__(self):
        return self.name

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    @property
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
    def __init__(self, op, operands):
        super().__init__()
        assert op in GATE_TYPES, f"Unsupported LogicOp: {op}"
        assert isinstance(op, str)
        self.name = op
        self.op = op
        self.operands = operands
        self.children = [
                inp if isinstance(inp, LogicTreeNode) else LogicHole(f"input_{i}")
                for i, inp in enumerate(operands)
        ]

    def __del__(self):
        log.info(f"[GC] LogicOp deleted: {self}")
    
    @property
    def expr_source(self):
        return None

    @property
    def delay(self):
        return 0

    #def label(self):
    #    return str(self.op)

    def default_label(self):
        return str(self.op)

    def to_json_dict(self):
        return {
            "type": self.__class__.__name__,
            "label": self.label(),
            "depth": self.depth,
            "delay": self.delay,
            "expr_source": self.expr_source,
            "children": [child.to_json_dict() for child in self.children],
        }

    def equals(self, other):
        if not isinstance(other, LogicOp):
            return False

        if self.op != other.op:
            return False
        if len(self.operands) != len(other.operands):
            return False

        # Commutative ops: Check operands ignoring order
        if self.op in COMMUTATIVE_OPS:
            self_sorted = sorted(self.operands, key=lambda x: str(x))
            other_sorted = sorted(self.operands, key=lambda x: str(x))
            return all(a.equals(b) for a, b in zip(self_sorted, other_sorted))

        # Non-commutative: preserve order
        return all(a.equals(b) for a, b in zip(self.operands, other.operands))

    def simplify(self):
        simplified_ops = [op.simplify() for op in self.operands]

        # Constant short-circuits
        if self.op == 'AND':
            if any(isinstance(op, LogicConst) and op.value == 0 for op in simplified_ops):
                return LogicConst(0)
            # Remove 1's
            simplified_ops = [op for op in simplified_ops if not (isinstance(op, LogicConst) and op.value == 1)]
        elif self.op == 'OR':
            if any(isinstance(op, LogicConst) and op.value == 1 for op in simplified_ops):
                return LogicConst(1)
            # Remove 0's
            simplified_ops = [op for op in simplified_ops if not (isinstance(op, LogicConst) and op.value == 0)]

        # Remove duplicates for idempotence
        unique_ops = []
        for op in simplified_ops:
            if all(not op.equals(o) for o in unique_ops):
                unique_ops.append(op)
        simplified_ops = unique_ops

        # Degenerate form: one operand left
        if len(simplified_ops) == 1:
            return simplified_ops[0]

        return LogicOp(self.op, simplified_ops)

    def __str__(self):
        return f"({f' {self.op} '.join(map(str, self.inputs()))})"

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    @property 
    def depth(self):
        if not self.children:
            return 0
        return 1 + max(inp.depth for inp in self.children)

    def to_verilog(self):
        if self.name == "NOT":
            log.debug(f" LogicOp::to_verilog() self.children[0]:{self.children[0]}, name: {self.name}")
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
        return f"LogicOp({self.op}, {self.operands})"

    def collect_input_names(self) -> set[str]:
        names = set()
        for c in self.children:
            names.update(c.collect_input_names())
        return names

