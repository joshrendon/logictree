import pytest

pytestmark = [pytest.mark.unit]

import unittest

from logictree.nodes.ops.gates import AndOp, NotOp, OrOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.transforms.simplify import simplify_logic_tree


class TestLogicSimplification(unittest.TestCase):

    def test_and_with_identity(self):
        a = LogicVar("a")
        const1 = LogicConst(1)
        op = AndOp(a, const1)
        simplified = simplify_logic_tree(op)
        #print("=======================")
        #print("Test AND with identity")
        #print("Original:")
        #print(pretty_print(op))
        #print("Simplified:", simplified)
        self.assertTrue(simplified.equals(a))

    def test_or_with_domination(self):
        a = LogicVar("a")
        const1 = LogicConst(1)
        op = OrOp(a, const1)
        #print("=======================")
        #print("Test OR with domination")
        #print("Original:")
        #print(pretty_print(op))
        simplified = simplify_logic_tree(op)
        #print("Simplified:", simplified)
        self.assertTrue(isinstance(simplified, LogicConst))
        self.assertEqual(simplified.value, 1)

    def test_double_negation(self):
        a = LogicVar("x")
        not1 = NotOp(NotOp(a))
        #print("=======================")
        #print("Test double negation")
        #print("Original:", not1)
        #print(pretty_print(not1))
        simplified = simplify_logic_tree(not1)
        #print(f"Simplified: {pretty_inline(simplified)}")
        self.assertTrue(simplified.equals(a))

    def test_idempotence(self):
        a = LogicVar("a")
        op = AndOp(a, a)
        #print("=======================")
        #print("Testing idempotence")
        #print(f"Original: {pretty_inline(op)}")
        simplified = simplify_logic_tree(op)
        #print(f"Simplified: {pretty_inline(simplified)}")
        self.assertTrue(simplified.equals(a))

if __name__ == "__main__":
    unittest.main()

