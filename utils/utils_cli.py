import json
import os


def write_golden_file(path, name, logic_hash, expr_str, inputs_flat, inputs_decl):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "name": name,
        "hash": logic_hash,
        "expr": expr_str,
        "inputs": {
            "flat": sorted(inputs_flat),
            "decl": inputs_decl or []
        }
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

