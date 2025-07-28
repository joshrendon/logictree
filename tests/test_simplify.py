import unittest
from logictree.nodes.ops.ops import LogicOp, LogicConst, LogicVar
from logictree.nodes.ops.gates import NotOp
from logictree.utils.display import pretty_print

class TestLogicSimplification(unittest.TestCase):

    def test_and_with_identity(self):
        a = LogicVar("a")
        const1 = LogicConst(1)
        op = LogicOp("AND", [a, const1])
        simplified = op.simplify()
        print("=======================")
        print("Test AND with identity")
        print("Original:")
        print(pretty_print(op))
        print("Simplified:", simplified)
        self.assertTrue(simplified.equals(a))

    def test_or_with_domination(self):
        a = LogicVar("a")
        const1 = LogicConst(1)
        op = LogicOp("OR", [a, const1])
        print("=======================")
        print("Test OR with domination")
        print("Original:")
        print(pretty_print(op))
        simplified = op.simplify()
        print("Simplified:", simplified)
        self.assertTrue(isinstance(simplified, LogicConst))
        self.assertEqual(simplified.value, 1)

    def test_double_negation(self):
        a = LogicVar("x")
        not1 = NotOp(NotOp(a))
        print("=======================")
        print("Test double negation")
        print("Original:", not1)
        print(pretty_print(not1))
        simplified = not1.simplify()
        print("Simplified:")
        print(pretty_print(simplified))
        self.assertTrue(simplified.equals(a))

    def test_idempotence(self):
        a = LogicVar("a")
        op = LogicOp("AND", [a, a])
        print("=======================")
        print("Testing idempotence")
        print("Original:")
        print(pretty_print(op))
        simplified = op.simplify()
        print("Simplified:", simplified)
        self.assertTrue(simplified.equals(a))

if __name__ == "__main__":
    unittest.main()

