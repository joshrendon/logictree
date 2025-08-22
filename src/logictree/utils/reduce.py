# logictree/utils/reduce.py
from typing import Dict, Tuple, Union, Optional
from .gate_factory import create_gate

def balance_logic_tree(tree):
    if isinstance(tree, ops.LogicOp):
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

#def balanced_tree_reduce(op_name, nodes):
#    """Builds a balanced binary tree of LogicOps over the inputs."""
#    if not nodes:
#        raise ValueError("Cannot reduce empty node list")
#
#    if len(nodes) == 1:
#        return nodes[0]
#
#    # Resolve to correct class
#    op_class = OP_CLASS_MAP.get(op_name.upper())
#    if op_class is None:
#        raise ValueError(f"Unknown logic operator: {op_name}")
#
#    mid = len(nodes) // 2
#    left = balanced_tree_reduce(op_name, nodes[:mid])
#    right = balanced_tree_reduce(op_name, nodes[mid:])
#    return op_class(left, right)
