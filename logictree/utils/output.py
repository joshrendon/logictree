from logictree.utils.display import to_dot
from logictree.utils.serialize import logic_tree_to_json
import json

def write_dot_to_file(node, filepath):
    dot_str = to_dot(node)
    with open(filepath, "w") as f:
        f.write(dot_str.source)

def write_json_to_file(node, filepath):

    if hasattr(node, "to_ir_dict"):
        data = node.to_ir_dict()
    else:
        data = logic_tree_to_json(node)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
