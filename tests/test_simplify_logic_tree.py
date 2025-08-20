from logictree.transforms.simplify import simplify_logic_tree
from logictree.nodes.ops.gates import AndOp, OrOp, NotOp, XorOp, XnorOp, NandOp, NorOp
from logictree.nodes.ops.ops import LogicConst, LogicVar

def test_and_true_identity():
    a = LogicVar("a")
    one = LogicConst(1)
    tree = AndOp(a, one)
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "a"

def test_or_false_identity():
    b = LogicVar("b")
    zero = LogicConst(0)
    tree = OrOp(b, zero)
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "b"

def test_double_negation():
    x = LogicVar("x")
    not1 = NotOp(x)
    not2 = NotOp(not1)
    simplified = simplify_logic_tree(not2)
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "x"

def test_and_true_identity():
    a = LogicVar("a")
    one = LogicConst(1)
    tree = AndOp(a, one)
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "a"

def test_and_false_annihilator():
    a = LogicVar("a")
    zero = LogicConst(0)
    tree = AndOp(a, zero)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicConst)
    assert simplified.value == 0

def test_or_false_identity():
    b = LogicVar("b")
    zero = LogicConst(0)
    tree = OrOp(b, zero)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "b"

def test_or_true_annihilator():
    b = LogicVar("b")
    one = LogicConst(1)
    tree = OrOp(b, one)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicConst)
    assert simplified.value == 1

def test_double_negation():
    x = LogicVar("x")
    not1 = NotOp(x)
    not2 = NotOp(not1)
    simplified = simplify_logic_tree(not2)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    print("dir:", dir(simplified))
    assert isinstance(simplified, LogicVar)
    assert simplified.name == "x"

def test_xor_with_zero():
    a = LogicVar("a")
    zero = LogicConst(0)
    tree = XorOp(a, zero)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicVar)
    assert simplified.equals(a)

def test_xnor_same_var():
    a = LogicVar("a")
    tree = XnorOp(a, a)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicConst)
    assert simplified.value == 1

def test_nand_with_one():
    a = LogicVar("a")
    one = LogicConst(1)
    tree = NandOp(a, one)
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, NotOp)
    assert simplified.operand.equals(a)

def test_nor_with_zero():
    b = LogicVar("b")
    zero = LogicConst(0)
    tree = NorOp(zero, b)
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, NotOp)
    assert simplified.operand.equals(b)

def test_and_with_zero_then_not():
    a = LogicVar("a")
    zero = LogicConst(0)
    inner = AndOp(a, zero)
    tree = NotOp(inner)
    simplified = simplify_logic_tree(tree)
    print("simlified tree:", simplified)
    print("Type:", type(simplified))
    assert isinstance(simplified, LogicConst)
    assert simplified.value == 1

def test_nested_or_and():
    a = LogicVar("a")
    one = LogicConst(1)
    inner = AndOp(a, one)      # → a
    tree = OrOp(inner, LogicConst(0))  # a | 0 → a
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.equals(a)

def test_double_xor_identity():
    a = LogicVar("a")
    tree = XorOp(XorOp(a, LogicConst(1)), LogicConst(1))  # (a ^ 1) ^ 1 = a
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.equals(a)

def test_deep_tree_mixed_ops():
    a = LogicVar("a")
    b = LogicVar("b")
    tree = OrOp(
        AndOp(a, LogicConst(1)),    # a
        AndOp(b, LogicConst(0))     # 0
    )  # → a | 0 → a
    simplified = simplify_logic_tree(tree)
    assert isinstance(simplified, LogicVar)
    assert simplified.equals(a)
