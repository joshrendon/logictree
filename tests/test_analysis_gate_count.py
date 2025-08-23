import pytest

pytestmark = [pytest.mark.unit]

import unittest

from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.utils.analysis import gate_count


class TestGateCount(unittest.TestCase):
    def test_simple_and(self):
        a = LogicVar("a")
        b = LogicVar("b")
        and_gate = AndOp(a, b)
        self.assertEqual(gate_count(and_gate), 1)

    def test_nested_ops(self):
        a = LogicVar("a")
        b = LogicVar("b")
        not_b = NotOp(b)
        or_gate = OrOp(a, not_b)
        top = AndOp(or_gate, LogicConst(1))
        self.assertEqual(gate_count(top), 3)  # AND + OR + NOT

    def test_constants_only(self):
        const_expr = LogicConst(0)
        self.assertEqual(gate_count(const_expr), 0)

if __name__ == '__main__':
    unittest.main()

