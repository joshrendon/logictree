# utils/ascii_tree.py
def logic_tree_to_ascii(node, indent: int = 0) -> str:
    """Recursively generate an ASCII tree representation of a logic tree."""
    indent_str = "  " * indent
    if hasattr(node, 'name'):
        label = node.name
    elif hasattr(node, 'value'):
        label = str(node.value)
    else:
        label = str(node)

    if not hasattr(node, 'inputs') or not node.inputs:
        return f"{indent_str}{label}"

    children = [logic_tree_to_ascii(child, indent + 1) for child in node.inputs if child is not None]
    return f"{indent_str}{label}\n" + "\n".join(children)

