import pytest

pytestmark = [pytest.mark.unit]

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.ops.ops import LogicConst, LogicVar


def make_assign(lhs_name, rhs_name):
    return LogicAssign(lhs=LogicVar(lhs_name), rhs=LogicVar(rhs_name))

def test_caseitem_label_rendering():
    # 1. Regular case item
    item1 = CaseItem(labels=[LogicConst(0)], default=False, body=[make_assign("y", "a")])
    assert item1.label() == "case 0"

    # 2. Multiple labels
    item2 = CaseItem(labels=[LogicConst(1), LogicConst(2)], default=False, body=[make_assign("y", "b")])
    assert item2.label() == "case 1, 2"

    # 3. Default case
    item3 = CaseItem(labels=[LogicConst("default")], default=True, body=[make_assign("y", "c")])
    assert item3.label() == "case default"

def test_casestatement_label_propagation():
    selector = LogicVar("s")

    case_stmt = CaseStatement(
        selector=selector,
        items=[
            CaseItem(labels=[LogicConst(0)], default=False, body=[make_assign("y", "a")]),
            CaseItem(labels=[LogicConst(1)], default=False, body=[make_assign("y", "b")]),
            CaseItem(labels=[LogicConst("default")], default=True, body=[make_assign("y", "c")])
        ]
    )

    # Check label string generation of each item inside CaseStatement
    expected_labels = ["case 0", "case 1", "case default"]
    actual_labels = [item.label() for item in case_stmt.items]
    assert actual_labels == expected_labels

    # Check selector rendering
    assert str(case_stmt.selector) == "s"

def test_case_statement_dot_and_json_outputs(tmp_path):
    from logictree.utils.output import write_dot_to_file, write_json_to_file

    selector = LogicVar("sel")
    y = LogicVar("y")

    case_stmt = CaseStatement(
        selector=selector,
        items=[
            CaseItem(labels=[LogicConst(0)], default=False, body=[LogicAssign(lhs=y, rhs=LogicVar("a"))]),
            CaseItem(labels=[LogicConst(1)], default=False, body=[LogicAssign(lhs=y, rhs=LogicVar("b"))]),
            CaseItem(labels=[LogicConst("default")], default=True, body=[LogicAssign(lhs=y, rhs=LogicVar("c"))])
        ]
    )

    # Export .dot file
    dot_path = tmp_path / "case_stmt.dot"
    write_dot_to_file(case_stmt, filepath=dot_path)
    assert dot_path.exists()
    assert dot_path.read_text().startswith("digraph")

    # Export .json file
    json_path = tmp_path / "case_stmt.json"
    write_json_to_file(case_stmt, filepath=json_path)
    assert json_path.exists()

    import json
    
    with open(json_path) as f:
        data = json.load(f)
    
    assert data["type"] == "CaseStatement"
    assert data["selector"]["type"] == "LogicVar"
    assert data["selector"]["name"] == "sel"
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 3
