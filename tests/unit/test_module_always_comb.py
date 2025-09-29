import pytest
from logictree.pipeline import lower_sv_text_to_logic
from logictree.nodes.control.alwaysblock import AlwaysKind
from logictree.nodes.control.assign import LogicAssign, ProceduralAssign
from logictree.nodes.struct.statement import BlockStatement
from logictree.nodes.ops.gates import OrOp
from logictree.utils.display import to_sympy_expr
from sympy import symbols, simplify, Piecewise
from sympy.logic.boolalg import ITE

def test_module_assign_and_always_comb():
    sv = r"""
    module m(input a, b, clk, output reg y, output z);
      assign z = a & b;

      always @* begin : comb_blk
        y = a | b;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    # Continuous assign should land in assignments
    assert "z" in m.assignments
    z_assign = m.assignments["z"]
    assert isinstance(z_assign, LogicAssign)
    #s = ab.body.statemetns[0]
    #assert s.blocking is True
    #assert z_assign.blocking is True
    #assert z_assign.lhs.name == "z"

    # Always block should land in always_blocks
    assert len(m.always_blocks) == 1
    ab = m.always_blocks[0]
    #assert ab.kind == AlwaysKind.COMB
    #assert ab.label == "comb_blk"

    # Always block body should contain a LogicAssign
    assert len(ab.body.statements) == 1
    assert isinstance(ab.body, BlockStatement), f"{type(s).__name__}"
    s = ab.body.statements[0]
    assert isinstance(s, ProceduralAssign)
    assert s.lhs.name == "y"
    assert isinstance(s.rhs, OrOp)

    #inner = s.statements[0]
    #assert isinstance(inner, LogicAssign)
    #assert inner.lhs.name == "y"
    #assert inner.blocking is True

    #assert s.lhs.name == "y"

    ## For procedural assigns, blocking=True
    #assert s.blocking is True


def test_module_always_seq_flagged():
    sv = r"""
    module m(input clk, input a, output reg y);
      always @(posedge clk) begin : seq_blk
        y <= a;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    assert len(m.always_blocks) == 1
    ab = m.always_blocks[0]
    assert ab.kind == AlwaysKind.SEQ
    assert ab.label == "seq_blk"

    # The assignment should be marked non-blocking
    s = ab.body.statements[0]
    assert isinstance(s, LogicAssign), f"{type(s).__name__}"
    assert s.blocking is False
    assert s.lhs.name == "y"

def test_module_always_multiple_assigns():
    sv = r"""
    module m(input a, b, output reg y, output reg z);
      always @* begin : multi_blk
        y = 0;
        if (a) y = 1;
        if (b) y = 2;
        z = a & b;
      end
    endmodule
    """
    mods = lower_sv_text_to_logic(sv)
    m = mods["m"]

    assert len(m.always_blocks) == 1
    ab = m.always_blocks[0]
    assert ab.label == "multi_blk"

    # Body should contain multiple statements
    stmts = ab.body.statements
    assert any(s.lhs.name == "y" for s in stmts)
    assert any(s.lhs.name == "z" for s in stmts)

    # SSA lowering: y should become nested ite (last-wins)
    y_assigns = [s for s in stmts if s.lhs.name == "y"]
    assert len(y_assigns) >= 2  # default + overrides

    # Run lowering to LogicTree IR and inspect final expression
    #y_expr = m.signal_map["y"].logic_expr.to_sympy()
    y_expr = to_sympy_expr(m.signal_map["y"])

    # Expect: y = ite(b, 2, ite(a, 1, 0))
    a, b = symbols("a b")
    #expected = (b & 1) * 2 + (~b & a) * 1 + (~b & ~a) * 0  # one encoding
    #expected = ITE(b, 2, ITE(a, 1, 0))
    expected = Piecewise(
        (2, b),
        (1, a),
        (0, True)
    )
    assert simplify(y_expr - expected) == 0
