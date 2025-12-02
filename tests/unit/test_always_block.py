from logictree.nodes.control.alwaysblock import AlwaysKind


def test_always_at_star_and_paren(lower_sv_text_to_logic):
    sv = r"""
    module m(input a, b, clk, output reg y, output reg z);
      always @* begin : blk1
        y = a & b;
      end

      always @(*) begin : blk2
        z = a | b;
      end

      always @(posedge clk) begin : blk3
        y <= a;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    assert len(m.always_blocks) == 3

    blk1, blk2, blk3 = m.always_blocks

    assert blk1.kind == AlwaysKind.COMB
    assert blk1.label == "blk1"

    assert blk2.kind == AlwaysKind.COMB
    assert blk2.label == "blk2"

    assert blk3.kind == AlwaysKind.SEQ
    assert blk3.label == "blk3"

    # Check assignments in comb
    y_assign = blk1.body.statements[0]
    assert y_assign.blocking is True

    z_assign = blk2.body.statements[0]
    assert z_assign.blocking is True

    # Check assignment in seq
    seq_assign = blk3.body.statements[0]
    assert seq_assign.blocking is False
