import json
import os


def write_analysis_results(
    results: dict, out_path: str = "output/analysis_results.json"
):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
