# logictree/utils.py

from .nodes import LogicOp

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
    return LogicOp(op_name, [left, right])

