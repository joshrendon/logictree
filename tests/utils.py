# tests/util.py
import itertools
import re

from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.ops.comparison import EqOp
from logictree.nodes.ops.gates import AndOp, NotOp, OrOp, XorOp
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect

# Nodes to skip because they don't implement or need these methods
EXCLUDED_CLASSES = {
    'LogicVar', 'LogicConst', 'LogicAssign', 'LogicHole',
    'IfStatement', 'FlattenedIfStatement', 'CaseStatement',
    'CaseItem', 'LogicOp',
}

def LogicConstSV(literal: str) -> LogicConst:
    """
    Shorthand for constructing a LogicConst from a SystemVerilog-style literal.

    Examples:
        LogicConstSV("3'b101")   -> LogicConst(value=5, width=3, base="b")
        LogicConstSV("8'd42")    -> LogicConst(value=42, width=8, base="d")
        LogicConstSV("'0")       -> LogicConst(value=0, width=1, base="b")
    """
    return LogicConst.from_sv_literal(literal)

def all_subclasses(cls):
    """Return the transitive closure of subclasses for a class."""
    seen = set()
    stack = [cls]
    while stack:
        base = stack.pop()
        for sub in base.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                stack.append(sub)
    return seen

def safe_instantiate(cls):
    """
    Try to construct a minimal valid instance of a LogicTreeNode subclass.
    Return the instance or None if we don't know how / it's not constructible.
    """
    try:
        # Known leaf-ish nodes
        if cls is LogicVar:
            return LogicVar("x")
        if cls is LogicConst:
            return LogicConst(0)

        # Common unary/binary gates
        if cls is NotOp:
            return NotOp(LogicVar("x"))
        if cls is AndOp:
            return AndOp(LogicVar("a"), LogicVar("b"))
        if cls is OrOp:
            return OrOp(LogicVar("a"), LogicVar("b"))

        # Unknown or control-structure nodes: best effort by signature guesses
        # If the class takes no args, try to call it; otherwise, skip.
        try:
            return cls()  # may work for some simple utility nodes
        except TypeError:
            return None
    except Exception:
        # If anything unexpected happens, skip this class
        return None

def _expr(node):
    """Unwrap LogicAssign to RHS; pass expressions unchanged."""
    return node.rhs if isinstance(node, LogicAssign) else node

def _is_mux_tree(node, sel_name: str, a_name: str, b_name: str) -> bool:
    """
    Check (s & b) | (~s & a) shape strictly.
    a_name is the value when sel==0, b_name when sel==1.
    """
    if not isinstance(node, OrOp):
        return False
    left, right = node.a, node.b
    # left must be AndOp(sel, b)
    if not isinstance(left, AndOp):
        return False
    if not (isinstance(left.a, LogicVar) and left.a.name == sel_name):
        return False
    if not (isinstance(_expr(left.b), LogicVar) and _expr(left.b).name == b_name):
        return False
    # right must be AndOp(~sel, a)
    if not isinstance(right, AndOp):
        return False
    if not (isinstance(right.a, NotOp) and isinstance(right.a.operand, LogicVar) and right.a.operand.name == sel_name):
        return False
    if not (isinstance(_expr(right.b), LogicVar) and _expr(right.b).name == a_name):
        return False
    return True

def eval_tree(root, inputs_dict):
    """Tiny interpreter for your LogicTree/IfStatement/LogicOp nodes."""
    # Implement using your node API: LogicConst/LogicVar/AndOp/OrOp/NotOp, IfStatement, etc.
    # Return bool/int for single-bit, tuple/bitvector for multi-bit as your IR dictates.
    raise NotImplementedError

def exhaustively_equal(f_root, g_root, input_vars):
    for bits in itertools.product([0,1], repeat=len(input_vars)):
        env = dict(zip(input_vars, bits))
        assert eval_tree(f_root, env) == eval_tree(g_root, env), f"Mismatch at {env}"

def _bit_name_index(bs):
    # Try structured fields first
    idx = getattr(bs, "index", None)
    var = getattr(bs, "var", None)
    name = None
    for a in ("name", "id", "identifier", "symbol", "label"):
        if var is not None and hasattr(var, a):
            name = getattr(var, a)
            break
    if name is None and isinstance(var, str):
        name = var
    # Fallback: parse from string like "s[3]"
    if name is None or idx is None:
        m = re.match(r"\s*([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]\s*$", str(bs))
        if m:
            name = name or m.group(1)
            if idx is None:
                idx = int(m.group(2))
    return name, idx

def _extract_eq_terms(rhs):
    """
    Recursively flatten an AND tree of EqOps(BitSelect, LogicConst)
    into a set of (bit_index, const_value) pairs.

    Example:  (s[0] == 0) & (s[1] == 1)
    → { (0, 0), (1, 1) }
    """
    terms = []

    def walk(node):
        if isinstance(node, AndOp):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, EqOp):
            lhs, rhs_const = node.operands
            assert isinstance(lhs, BitSelect)
            assert isinstance(lhs.base, LogicVar)
            assert isinstance(rhs_const, LogicConst)
            terms.append((lhs.index, rhs_const.value))
        else:
            raise AssertionError(f"Unexpected node type in eq expansion: {node}")

    walk(rhs)
    return set(terms)

def assert_eq_const_terms(rhs, const_value: int, width: int, varname="s"):
    """
    Assert that `rhs` encodes the equality check: var == const_value
    over a bit-vector of given `width`.

    Args:
        rhs: the lowered LogicTree expression
        const_value: integer constant (e.g. 9 for 4'b1001)
        width: number of bits in the vector
        varname: name of the LogicVar being compared

    Example:
        assert_eq_const_terms(rhs, 9, 4, "s")
    """
    terms = _extract_eq_terms(rhs)

    expected = set()
    for i in range(width):
        bit_val = (const_value >> i) & 1
        expected.add((i, bit_val))

    assert terms == expected, (
        f"Unexpected terms for {varname} == {width}'b{const_value:0{width}b}: {terms}"
    )

def assert_neq_const_terms(rhs, const_value: int, width: int, varname="s"):
    """
    Assert that `rhs` encodes the inequality check: var != const_value
    over a bit-vector of given `width`.

    It works by confirming the expression is equivalent to:
        NOT(AND(s[i] == bit_val for each i in range(width)))

    Args:
        rhs: the lowered LogicTree expression
        const_value: integer constant (e.g. 9 for 4'b1001)
        width: number of bits in the vector
        varname: name of the LogicVar being compared
    """
    # Ensure the top node is a NotOp
    assert isinstance(rhs, NotOp), (
        f"Expected NotOp for {varname} != {const_value}, got {type(rhs)}"
    )

    inner = rhs.child

    # The inner node should expand to AND of equalities
    terms = []
    def walk(node):
        if isinstance(node, AndOp):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, EqOp):
            lhs, rhs_const = node.operands
            assert isinstance(lhs, BitSelect)
            assert lhs.base.name == varname
            assert isinstance(rhs_const, LogicConst)
            terms.append((lhs.index, rhs_const.value))
        else:
            raise AssertionError(f"Unexpected node in neq expansion: {node}")

    walk(inner)

    expected = set()
    for i in range(width):
        bit_val = (const_value >> i) & 1
        expected.add((i, bit_val))

    assert set(terms) == expected, (
        f"Unexpected terms for {varname} != {width}'b{const_value:0{width}b}: {terms}"
    )

def _unary_operand(n):
    # many NotOp nodes store .child or .operand; try both
    return getattr(n, "child", getattr(n, "operand", None))

def flatten_and(n):
    """Return list of AND-tree leaves in-order."""
    if isinstance(n, AndOp):
        return flatten_and(n.left) + flatten_and(n.right)
    return [n]

def flatten_or(n):
    if isinstance(n, OrOp):
        return flatten_or(n.left) + flatten_or(n.right)
    return [n]

def leaves(nodes):
    """Identity helper to emphasize intent (already leaf-ish)."""
    return nodes

def _name_of(node):
    # Try node.name, else node.var.name (BitSelect), else None
    return getattr(node, "name", getattr(getattr(node, "var", node), "name", None))

def gate_count(n):
    """Count gate node types in a binary/unary tree."""
    counts = {"AND":0, "OR":0, "XOR":0, "NOT":0}

    def walk(x):
        if isinstance(x, AndOp):
            counts["AND"] += 1
            walk(x.left)
            walk(x.right)
        elif isinstance(x, OrOp):
            counts["OR"] += 1
            walk(x.left)
            walk(x.right)
        elif isinstance(x, XorOp):
            counts["XOR"] += 1
            walk(x.left)
            walk(x.right)
        elif isinstance(x, NotOp):
            counts["NOT"] += 1
            o = _unary_operand(x)
            if o is not None: walk(o)
        else:
            # leaf-ish (BitSelect, Id, Const, etc.)
            pass
    walk(n)
    return counts

def _unary_operand(n):
    # Support either .child or .operand
    return getattr(n, "child", getattr(n, "operand", None))

def _bit_index(bs):
    # Try common attribute names first
    for attr in ("index", "idx", "bit", "pos", "i"):
        if hasattr(bs, attr):
            return getattr(bs, attr)
    # Fallback: parse from string like "s[12]"
    m = re.search(r"\[(\d+)\]", str(bs))
    return int(m.group(1)) if m else None

def _bit_base(bs):
    # The base signal under the bit-select
    for attr in ("var", "vector", "target", "expr", "base"):
        if hasattr(bs, attr):
            return getattr(bs, attr)
    return None

def _logicvar_name(x):
    # Accept LogicVar(.name), plain strings, or parse from str(x)
    if hasattr(x, "name"):
        return x.name
    if isinstance(x, str):
        return x
    # Fallback parse: "s[3]" -> "s", or "LogicVar(s)" -> "s"
    sx = str(x)
    m = re.match(r"([A-Za-z_]\w*)\[\d+\]", sx) or re.match(r".*?\(([^)]+)\)", sx)
    return m.group(1) if m else None

def _literal_sig(n, expected_name: str | None = None):
    """Return (name, index, is_positive) for LogicVar, BitSelect, or Not(...)."""
    is_pos = True
    if isinstance(n, LogicVar):
        return (n.name, None, True)

    if isinstance(n, NotOp):
        n = _unary_operand(n)
        is_pos = False

    if isinstance(n, BitSelect):
        base = _bit_base(n)
        name = _logicvar_name(base)
        idx = _bit_index(n)
        return (name, idx, is_pos)

    # Fallback: not a literal signal
    return (None, None, is_pos)


def _flatten_and(n):
    """Flatten a left-nested chain of AndOp into a list of leaf terms."""
    if isinstance(n, AndOp):
        return _flatten_and(n.left) + _flatten_and(n.right)
    return [n]


def literal_sig_set(n, only_name=None):
    """
    Collect a set of literal signals seen in a conjunction.
    Returns {(name, is_positive)} for scalar vars,
    or {(name[idx], is_positive)} for bit selects.
    """
    out = set()
    for t in _flatten_and(n):
        name, idx, is_pos = _literal_sig(t)
        if name is None:
            continue
        if only_name is None or name == only_name:
            if idx is None:
                out.add((name, is_pos))
            else:
                out.add((f"{name}[{idx}]", is_pos))
    return out
