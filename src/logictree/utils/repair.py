# LogicTree utils that repair the tree structure/nodes
from logictree.nodes.base import LogicTreeNode
from logictree.nodes.ops import LogicOp
from logictree.nodes.hole import LogicHole

def repair_tree_inputs(node):
    if isinstance(node, LogicOp):
        for i, inp in enumerate(node.inputs):
            if inp is None:
                print(f"[repair] Inserting LogicHole at input {i} of {node.name}")
                node.inputs[i] = LogicHole(f"missing_input_{i}")
            else:
                repair_tree_inputs(inp)
