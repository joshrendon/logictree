from .gate_factory import create_gate


def balance_logic_tree(tree):
    try:
        balanced_children = [balance_logic_tree(child) for child in tree.children]
        return balanced_tree_reduce(tree.op, balanced_children)
    except AttributeError:
        # Base case: leaf node without .children/.op
        return tree


def balanced_tree_reduce(op_name, inputs):
    """Builds a balanced binary tree of LogicOps over the inputs."""
    if len(inputs) == 1:
        return inputs[0]
    mid = len(inputs) // 2
    left = balanced_tree_reduce(op_name, inputs[:mid])
    right = balanced_tree_reduce(op_name, inputs[mid:])
    return create_gate(op_name, left, right)
