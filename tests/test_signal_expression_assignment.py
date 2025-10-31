import logging

import pytest

pytestmark = [pytest.mark.unit]

from pprint import pprint

from logictree.nodes.control.assign import LogicAssign
from logictree.pipeline import lower_sv_text_to_logic
from logictree.utils.display import pretty_print

log = logging.getLogger(__name__)


def test_simple_module():
    code = "module foo(input logic a, output logic b); assign b = a; endmodule"
    module_map = lower_sv_text_to_logic(code)
    pprint(module_map)

    assert "foo" in module_map
    mod = module_map["foo"]
    assign = mod.get_assignment("b")
    log.info(f"assign: {pretty_print(assign)}")
    assert isinstance(assign, LogicAssign)
    log.info(f"lhs: {assign.lhs.name}")
    log.info(f"rhs: {assign.rhs.name}")
    assert assign.lhs.name == "b"
    assert assign.rhs.name == "a"

