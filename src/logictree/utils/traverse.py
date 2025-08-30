from logictree.nodes.ops.ops import LogicOp, LogicVar


def collect_logic_vars(node):
    """Yield all LogicVar nodes inside a tree."""
    if isinstance(node, LogicVar):
        yield node
    elif isinstance(node, LogicOp):
        for child in node.children:
            yield from collect_logic_vars(child)
