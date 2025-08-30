import logging

import pytest

from logictree.api import lower_sv_to_logic as lower_sv_text_to_logic
from logictree.utils.output import render_png, write_dot_to_file
from tests.utils.viz_helpers import assert_viz

log = logging.getLogger(__name__)

pytestmark = [pytest.mark.unit]

def test_if_elseif_else_three_way_viz(tmp_path):
    sv = """
    module m(input logic s0,s1, d0,d1,d2, output logic y);
      always_comb begin
        if (s0) y = d0;
        else if (s1) y = d1;
        else y = d2;
      end
    endmodule
    """

    module = lower_sv_text_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs

    out_file = tmp_path / "mux.dot"
    write_dot_to_file(rhs, filepath=out_file)
    log.debug("out_file:%s", out_file.read_text())
    log.debug(f"tmp_path is {tmp_path}")

    assert out_file.exists()
    text = out_file.read_text()
    assert text.startswith("digraph")
    # loose check for structure
    assert "AND" in text or "MUX" in text or "OR" in text

def test_if_elseif_else_three_way_viz_render_png(tmp_path):
    sv = """
    module m(input logic s0,s1, d0,d1,d2, output logic y);
      always_comb begin
        if (s0) y = d0;
        else if (s1) y = d1;
        else y = d2;
      end
    endmodule
    """

    module = lower_sv_text_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs

    render_png(rhs, name="if_mux")

def test_if_else_if_three_way_viz_helper(tmp_path):
    sv = """
    module m(input logic s0,s1, d0,d1,d2, output logic y);
      always_comb begin
        if (s0) y = d0;
        else if (s1) y = d1;
        else y = d2;
      end
    endmodule
    """

    module = lower_sv_text_to_logic(sv)["m"]
    rhs = module.assignments["y"].rhs
    png = assert_viz(rhs, "if_else_demo")
    print(f"Visualization written to {png}")
