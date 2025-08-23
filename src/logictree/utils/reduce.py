from logictree.nodes.ops.ops import LogicOp
from .gate_factory import create_gate

def balance_logic_tree(tree):
    if isinstance(tree, LogicOp):
        balanced_children = [balance_logic_tree(child) for child in tree.children]
        return balanced_tree_reduce(tree.op, balanced_children)
    return tree

def balanced_tree_reduce(op_name, inputs):
    """Builds a balanced binary tree of LogicOps over the inputs."""
    if len(inputs) == 1:
        return inputs[0]
    mid = len(inputs) // 2
    left = balanced_tree_reduce(op_name, inputs[:mid])
    right = balanced_tree_reduce(op_name, inputs[mid:])
    return create_gate(op_name, left, right)

