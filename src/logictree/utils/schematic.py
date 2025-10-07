from pathlib import Path
import schemdraw
from schemdraw.parsing import logicparse
import re
import logging
from logictree.transforms.to_primitives import to_primitives_logic_tree

log = logging.getLogger(__name__)

CONST_RE = re.compile(r"\d+'d(\d+)")

def render_schematic(node, filename: str | Path = "schematic.png") -> Path:
    """
    Render a schematic diagram from a LogicTree node using schemdraw.
    Converts LogicTree -> primitives, sanitizes constants, and feeds into logicparse.
    """
    prim = to_primitives_logic_tree(node)
    prim_list = prim if isinstance(prim, list) else [prim]
    #expr_str = str(prim)

    # Replace SystemVerilog-style constants like 2'd3, 4'd0, etc. with just the number
    #expr_clean = CONST_RE.sub(r"\1", expr_str)

    # Map operators into logicparse syntax
    expr_for_draw = []
    for e in prim_list:
        expr_str = str(e)
        expr_clean = CONST_RE.sub(r"\1", expr_str)
        expr_schem = (
            expr_clean
            .replace("~", " not ")
            .replace("&", " and ")
            .replace("|", " or ")
            .replace("1", " true ")
            .replace("0", " false ")
        )
        expr_for_draw.append(expr_schem)

    log.info(f"render_schematic() expr_for_draw: {expr_for_draw}")

    out_path = Path(filename)
    #with schemdraw.Drawing(file=out_path, show=True) as d:
    #    logicparse(expr_for_draw, outlabel="y")
    #    d.save(out_path)

    with schemdraw.Drawing(file=out_path, show=False) as d:
        for i, expr in enumerate(expr_for_draw):   # exprs = list from to_primitives()
            y_label = f"y[{i}]"
            logicparse(expr, outlabel=y_label)
            d.move(0,-10)
        d.save(out_path)


    return out_path
