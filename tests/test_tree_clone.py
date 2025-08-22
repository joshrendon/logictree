import pytest
pytestmark = [pytest.mark.unit]
from logictree.nodes.ops.ops import LogicVar, LogicConst
from logictree.nodes.control.case import CaseStatement, CaseItem
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp
from logictree.nodes.control.ifstatement import IfStatement
from logictree.transforms.case_to_if import case_to_if_tree
from logictree.transforms.simplify import simplify_logic_tree
from tests.utils import _is_mux_tree, _expr
from logictree.utils.display import pretty_inline
import logging
log = logging.getLogger(__name__)

def _two_way_case(left_expr, right_expr):
    # out = (s ? right_expr : left_expr)
    s = LogicVar("s")
    i0 = CaseItem(match=LogicConst(0),
                  labels=[LogicConst(0)], 
                  body=LogicAssign("out", left_expr),
                  default=False)
    i1 = CaseItem(match=LogicConst(1),
                  labels=[LogicConst(1)],
                  body=LogicAssign("out", right_expr),
                  default=False)
    return CaseStatement(selector=s, items=[i0, i1])

def test_case_lowers_to_if_then_mux_and_simplifies_to_aoi():
    case_stmt = _two_way_case(LogicVar("a"), LogicVar("b"))

    # 1) default path: Case -> IfStatement
    lowered_if = case_to_if_tree(case_stmt, mode="if")
    log.debug(f"case to IfStatement: {pretty_inline(lowered_if)}")
    assert isinstance(lowered_if, IfStatement)

    # 2) mux path: Case -> Or(And(s,b), And(~s,a))
    mux_expr = case_to_if_tree(case_stmt, mode="mux")
    log.debug(f"Case -> MUX Tree: {pretty_inline(mux_expr)}")
    assert _is_mux_tree(mux_expr, sel_name="s", a_name="a", b_name="b")

    # 3) simplify should keep mux form for non-constant arms
    simplified = simplify_logic_tree(mux_expr)
    log.debug(f"simplify_logic_tree(mux_expr): {pretty_inline(simplified)}")
    assert _is_mux_tree(simplified, sel_name="s", a_name="a", b_name="b")

def test_mux_simplifies_with_constant_arm_to_expected_form():
    # out = (s ? b : 0) -> (s & b) | (~s & 0) -> (s & b)
    case_stmt = _two_way_case(LogicConst(0), LogicVar("b"))
    mux_expr = case_to_if_tree(case_stmt, mode="mux")
    simplified = simplify_logic_tree(mux_expr)
    # Expect a strict And(s, b)
    from logictree.nodes.ops.gates import AndOp
    assert isinstance(simplified, AndOp)
    assert isinstance(simplified.a, LogicVar) and simplified.a.name == "s"
    assert isinstance(_expr(simplified.b), LogicVar) and _expr(simplified.b).name == "b"

    # out = (s ? 1 : a) -> (s & 1) | (~s & a) -> s | (~s & a)  (still a mux-y AOI form)
    case_stmt2 = _two_way_case(LogicVar("a"), LogicConst(1))
    mux_expr2 = case_to_if_tree(case_stmt2, mode="mux")
    simplified2 = simplify_logic_tree(mux_expr2)
    # We at least expect an Or node with a plain 's' present
    from logictree.nodes.ops.gates import OrOp
    assert isinstance(simplified2, OrOp)
    has_s = (isinstance(simplified2.a, LogicVar) and simplified2.a.name == "s") or \
            (isinstance(simplified2.b, LogicVar) and simplified2.b.name == "s")
    assert has_s

def test_case_to_if_returns_ifstatement_by_default():
    case_stmt = _two_way_case(LogicVar("a"), LogicVar("b"))
    lowered = case_to_if_tree(case_stmt)  # default path
    assert isinstance(lowered, IfStatement)
    # original should remain a CaseStatement
    assert isinstance(case_stmt, CaseStatement)

def test_case_to_if_mux_mode_and_simplify_no_constants():
    case_stmt = _two_way_case(LogicVar("a"), LogicVar("b"))
    mux_expr = case_to_if_tree(case_stmt, mode="mux")
    # Structure before simplification: (s & b) | (~s & a)
    assert isinstance(mux_expr, OrOp)
    assert isinstance(mux_expr.a, AndOp)
    assert isinstance(mux_expr.b, AndOp)
    assert isinstance(mux_expr.a.a, LogicVar)      # s
    assert isinstance(mux_expr.a.b, LogicVar)      # b
    assert isinstance(mux_expr.b.a, NotOp)         # ~s
    assert isinstance(mux_expr.b.b, LogicVar)      # a

    simplified = simplify_logic_tree(mux_expr)
    # Still an expression (not turned back into IfStatement)
    assert not isinstance(simplified, IfStatement)

@pytest.mark.parametrize("left_is_const, const_val", [(True, 0), (False, 1)])
def test_case_to_if_mux_simplifies_with_constant_arm(left_is_const, const_val):
    # Build case with one constant arm
    if left_is_const:
        # out = (s ? b : 0) -> (s & b) | (~s & 0) -> s & b
        case_stmt = _two_way_case(LogicConst(const_val), LogicVar("b"))
    else:
        # out = (s ? 1 : a) -> (s & 1) | (~s & a) -> s | (~s & a)
        case_stmt = _two_way_case(LogicVar("a"), LogicConst(const_val))

    mux_expr = case_to_if_tree(case_stmt, mode="mux")
    simplified = simplify_logic_tree(mux_expr)

    if left_is_const:  # expect AndOp(s, b)
        assert isinstance(simplified, AndOp)
        assert isinstance(simplified.a, LogicVar) and simplified.a.name == "s"
        assert isinstance(simplified.b, LogicVar) and simplified.b.name == "b"
    else:
        # We at least expect (s & 1) to become s; top-level should have s present in OR
        assert isinstance(simplified, OrOp)
        names = []
        for node in (simplified.a, simplified.b):
            if isinstance(node, LogicVar):
                names.append(node.name)
        assert "s" in names

