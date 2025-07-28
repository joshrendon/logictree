from logictree.nodes import ops, control, base, hole
from typing import Dict, Tuple, Union, Optional

def balance_logic_tree(tree):
    if isinstance(tree, ops.LogicOp):
        balanced_children = [balance_logic_tree(child) for child in tree.children]
        return balanced_tree_reduce(tree.op, balanced_children)
    return tree

def balanced_tree_reduce(op_name, inputs):
    """Builds a balanced binary tree of LogicOps over the inputs."""
    if not inputs:
        raise ValueError("Cannot reduce empty input list")

    if len(inputs) == 1:
        return inputs[0]

    # Build binary tree recursively
    mid = len(inputs) // 2
    left = balanced_tree_reduce(op_name, inputs[:mid])
    right = balanced_tree_reduce(op_name, inputs[mid:])
    return ops.LogicOp(op_name, [left, right])
