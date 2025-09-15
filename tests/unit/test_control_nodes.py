from logictree.constants import EMPTY_BRANCH


def test_empty_branch_singleton():
    a = EMPTY_BRANCH
    b = EMPTY_BRANCH
    assert a is b
    assert repr(a) == "EmptyBranch()"
    assert a.to_verilog() == "1'b0"
