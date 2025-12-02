import pytest

import subprocess
import os
from pathlib import Path

pytestmark = pytest.mark.skip("Temporarily disabiling CLI lowering test")
@pytest.mark.integration
@pytest.mark.cli
def test_cli_lower_if():
    input_sv = Path("golden_circuits/if_tree_simple.sv")
    module_name = "if_tree_simple"
    output_path = Path("output") / f"{module_name}.png"

    # Remove old file if present
    if output_path.exists():
        output_path.unlink()

    result = subprocess.run([
        "logictree",
        str(input_sv),
        "--lowering_trace",
        "--pretty_print",
        "--to_ascii",
        "--to_png",
        "--loglevel", "debug"
    ], capture_output=True, text=True)

    print(result.stdout)
    print(result.stderr)

    assert result.returncode == 0, "CLI failed to run successfully"
    assert output_path.exists(), f"{output_path} was not created"
