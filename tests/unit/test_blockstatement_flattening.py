
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.struct.statement import BlockStatement
from logictree.pipeline import lower_sv_text_to_logic


def test_no_nested_blockstatements_in_always_body():
    sv = r"""
    module m(input a, b, output reg y);
      always @* begin : blk
        y = a | b;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]
    ab = m.always_blocks[0]

    assert isinstance(ab.body, BlockStatement)
    for stmt in ab.body.statements:
        # No nested block statements
        assert not isinstance(stmt, BlockStatement), "Unexpected nested BlockStatement"
        assert isinstance(stmt, LogicAssign)
