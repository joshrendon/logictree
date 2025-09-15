# tests/util.py
import itertools
import logging
import re
from collections import defaultdict

from logictree.nodes.base.base import LogicTreeNode
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.hole.hole import LogicHole
from logictree.nodes.ops.comparison import EqOp, NeqOp
from logictree.nodes.ops.empty import EmptyBranch
from logictree.nodes.ops.gates import AndOp, NandOp, NorOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.types import GATE_TYPES

log = logging.getLogger(__name__)

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
        # --- leaf-ish ---
        if cls is LogicVar:
            return LogicVar("x")
        if cls is LogicConst:
            return LogicConst(0)

        # --- unary ---
        if cls is NotOp:
            return NotOp(LogicVar("x"))

        # --- binary/n-ary gates ---
        if cls in (AndOp, OrOp, XorOp, XnorOp, NandOp, NorOp, EqOp, NeqOp):
            return cls(LogicVar("a"), LogicVar("b"))

        # --- mux ---
        if cls is LogicMux:
            return LogicMux(selector=LogicVar("s"),
                            if_true=LogicConst(0),
                            if_false=LogicConst(1))

        # --- selects ---
        if cls is BitSelect:
            return BitSelect(base=LogicVar("v"), index=LogicConst(2), width=0)
        if cls is PartSelect:
            return PartSelect(base=LogicVar("v"), msb=LogicConst(3), lsb=LogicConst(0))
        if cls is Concat:
            return Concat([LogicVar("a"), LogicVar("b")])

        # --- control/structural ---
        if cls is LogicAssign:
            return LogicAssign(lhs=LogicVar("y"), rhs=LogicConst(1))
        if cls is IfStatement:
            return IfStatement(cond=LogicVar("c"),
                               then_branch=LogicConst(1),
                               else_branch=LogicConst(0))
        if cls is CaseItem:
            return CaseItem(match_value=LogicConst(0),
                            statement=LogicAssign(LogicVar("y"), LogicConst(1)))
        if cls is CaseStatement:
            return CaseStatement(
                selector=LogicVar("s"),
                case_items=[CaseItem(LogicConst(0),
                                     LogicAssign(LogicVar("y"), LogicConst(1)))]
            )
        if cls is EmptyBranch:
            return EmptyBranch()
        if cls is LogicHole:
            return LogicHole()

        # --- fallback ---
        try:
            print(f"!!!INFO!!!: safe_instantiate() type(cls): {type(cls).__name__}, cls.name: {cls.__name__}")
            return cls()
        except TypeError:
            return None
    except Exception as e:
        print(f"!!!INFO!!!: safe_instantiate failed for {cls.__name__}: {e}")
        return None
#def safe_instantiate(cls):
#    """
#    Try to construct a minimal valid instance of a LogicTreeNode subclass.
#    Return the instance or None if we don't know how / it's not constructible.
#    """
#    try:
#        # Known leaf-ish nodes
#        if cls is LogicVar:
#            return LogicVar("x")
#        if cls is LogicConst:
#            return LogicConst(0)
#
#        # Common unary/binary gates
#        if cls is NotOp:
#            return NotOp(LogicVar("x"))
#        if cls is AndOp:
#            return AndOp(LogicVar("a"), LogicVar("b"))
#        if cls is OrOp:
#            return OrOp(LogicVar("a"), LogicVar("b"))
#
#        # Unknown or control-structure nodes: best effort by signature guesses
#        # If the class takes no args, try to call it; otherwise, skip.
#        try:
#            print(f"!!!INFO!!!: safe_instantiate() type(cls): {type(cls).__name__}, cls.name: {cls.__name__}")
#            return cls()  # may work for some simple utility nodes
#        except TypeError:
#            return None
#    except Exception:
#        # If anything unexpected happens, skip this class
#        return None

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

def _to_int(idx):
    return int(idx.value) if hasattr(idx, "value") else int(idx)

def _extract_eq_terms(rhs):
    terms = set()

    def walk(node):
        if isinstance(node, AndOp):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, EqOp):
            lhs, rhs_const = node.operands
            assert isinstance(lhs, BitSelect)
            terms.add((_to_int(lhs.index), _to_int(rhs_const)))
        else:
            raise AssertionError(f"Unexpected node: {node}")

    walk(rhs)
    return terms
#def _extract_eq_terms(rhs):
#    """
#    Recursively flatten an AND tree of EqOps(BitSelect, LogicConst)
#    into a set of (bit_index, const_value) pairs.
#
#    Example:  (s[0] == 0) & (s[1] == 1)
#    → { (0, 0), (1, 1) }
#    """
#    terms = []
#
#    def walk(node):
#        if isinstance(node, AndOp):
#            walk(node.left)
#            walk(node.right)
#        elif isinstance(node, EqOp):
#            lhs, rhs_const = node.operands
#            assert isinstance(lhs, BitSelect)
#            assert isinstance(lhs.base, LogicVar)
#            assert isinstance(rhs_const, LogicConst)
#            terms.append((lhs.index, rhs_const.value))
#        else:
#            raise AssertionError(f"Unexpected node type in eq expansion: {node}")
#
#    walk(rhs)
#    return set(terms)

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

def assert_neq_const_terms(rhs, const_value: int, width: int, varname="s", lo: int = 0):
    """
    Assert that `rhs` encodes the inequality check: var != const_value
    over a bit-vector of given `width`, starting at bit index `lo`.

    Accepts either:
      - Old form:  NotOp(AndOp(EqOp(...), ...))
      - New form:  OrOp(NeqOp(...), NeqOp(...), ...)

    Args:
        rhs: the lowered LogicTree expression
        const_value: integer constant (e.g. 9 for 4'b1001)
        width: number of bits in the vector slice
        varname: name of the LogicVar being compared
        lo: starting bit index (default 0 for [width-1:0])
    """
    terms = []

    def walk_and(node):
        if isinstance(node, AndOp):
            walk_and(node.left)
            walk_and(node.right)
        elif isinstance(node, EqOp):
            lhs, rhs_const = node.operands
            assert isinstance(lhs, BitSelect)
            assert lhs.base.name == varname
            assert isinstance(rhs_const, LogicConst)
            terms.append((int(lhs.index.value), rhs_const.value))
        else:
            raise AssertionError(f"Unexpected node in And->Eq expansion: {node}")

    def walk_or(node):
        if isinstance(node, OrOp):
            walk_or(node.left)
            walk_or(node.right)
        elif isinstance(node, NeqOp):
            lhs, rhs_const = node.operands
            assert isinstance(lhs, BitSelect)
            assert lhs.base.name == varname
            assert isinstance(rhs_const, LogicConst)
            terms.append((int(lhs.index.value), rhs_const.value))
        else:
            raise AssertionError(f"Unexpected node in Or->Neq expansion: {node}")

    if isinstance(rhs, NotOp):
        walk_and(rhs.operand)
    elif isinstance(rhs, OrOp):
        walk_or(rhs)
    else:
        raise AssertionError(
            f"Expected NotOp or OrOp for {varname} != {const_value}, got {type(rhs)}"
        )

    # Now check expected terms with offset
    for i in range(width):
        expected_val = (const_value >> i) & 1
        bit_index = lo + i
        assert (bit_index, expected_val) in terms, (
            f"Missing term for bit {bit_index} == {expected_val} in {terms}"
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

def gate_count(root):
    """Count logic gates in the expression tree rooted at `root`."""
    counts = defaultdict(int)

    def walk(node):
        if isinstance(node, AndOp):
            counts["AND"] += 1
            log.info(f"Counted AndOp, count: {counts}")
            walk(node.a)
            walk(node.b)

        elif isinstance(node, OrOp):
            counts["OR"] += 1
            log.info(f"Counted OrOp, count: {counts}")
            walk(node.a)
            walk(node.b)

        elif isinstance(node, XorOp):
            counts["XOR"] += 1
            log.info(f"Counted XorOp, count: {counts}")
            walk(node.a)
            walk(node.b)

        elif isinstance(node, NotOp):
            counts["NOT"] += 1
            log.info(f"Counted NotOp, count: {counts}")
            walk(node.child)

        elif isinstance(node, EqOp):
            counts["EQ"] += 1
            log.info(f"Counted EqOp, count: {counts}")
            walk(node.lhs)
            walk(node.rhs)

        elif isinstance(node, NeqOp):
            counts["NEQ"] += 1
            log.info(f"Counted NeqOp, count: {counts}")
            walk(node.lhs)
            walk(node.rhs)

        elif isinstance(node, BitSelect):
            log.info("Reached BitSelect")
            walk(node.base)
            walk(node.index)

        elif isinstance(node, (LogicVar, LogicConst)):
            # Leaf nodes – nothing to count or recurse
            log.info("Counted LogicVar or LogicConst")

        elif hasattr(node, "get_children"):
            log.info(f"Visiting children of unknown node: {type(node).__name__}")
            for child in node.get_children():
                walk(child)

        else:
            log.warning(f"[gate_count] Unexpected node type: {type(node).__name__}")
            log.warning(f"node: {node}")

    walk(root)

    # Ensure all gate types are present in output
    for gate in GATE_TYPES:
        counts[gate]  # This forces defaultdict to initialize missing keys to 0

    return dict(counts)
#def gate_count(root):
#    """Count logic gates in the expression tree rooted at `root`."""
#    counts = defaultdict(int)
#
#    def walk(node):
#        if isinstance(node, AndOp):
#            counts["AND"] += 1
#            log.info(f"Counted AndOp, count: {counts}")
#            walk(node.a)
#            walk(node.b)
#        elif isinstance(node, OrOp):
#            counts["OR"] += 1
#            log.info(f"Counted OrOp, count: {counts}")
#            walk(node.a)
#            walk(node.b)
#        elif isinstance(node, XorOp):
#            counts["XOR"] += 1
#            log.info(f"Counted XorOp, count: {counts}")
#            walk(node.a)
#            walk(node.b)
#        elif isinstance(node, NotOp):
#            counts["NOT"] += 1
#            log.info(f"Counted NotOp, count: {counts}")
#            operand = getattr(node, "child", getattr(node, "operand", None))
#            if operand:
#                walk(operand)
#        elif isinstance(node, BitSelect):
#            log.info(f"Reached BitSelect")
#            walk(node.base)
#            walk(node.index)
#        elif isinstance(node, (LogicVar, LogicConst)):
#            log.info(f"Counted LogicVar or LogicConst")
#            # Leaf node — stop recursion
#            return
#        elif isinstance(node, EqOp):
#            counts["EQ"] += 1
#            log.info(f"Counted EqOp, count {counts}")
#            walk(node.lhs)
#            walk(node.rhs)
#        elif isinstance(node, NeqOp):
#            counts["NEQ"] += 1
#            log.info(f"Counted NeqOp, count {counts}")
#            walk(node.lhs)
#            walk(node.rhs)
#        elif hasattr(node, "get_children"):
#            log.info(f"Counted node that has attr get_children()")
#            # Unknown node — safe fallback
#            for child in node.get_children():
#                walk(child)
#        #elif hasattr(node, "children"):
#        #    log.info(f"Counted node that has attr children")
#        #    # Unknown node — safe fallback
#        #    for child in node.children:
#        #        walk(child)
#        else:
#            # Log unexpected node type
#            log.info(f"[gate_count] Unexpected node type: {type(node).__name__}")
#            log.info(f"node: {node}")
#
#    walk(root)
#    
#    # Normalize to include all gate types even if count is 0
#    for gate in GATE_TYPES:
#        counts[gate]
#
#    return dict(counts)
#def gate_count(n):
#    """Count gate node types in a binary/unary tree."""
#    counts = defaultdict(int) #{"AND":0, "OR":0, "XOR":0, "NOT":0}
#
#    def walk(x):
#        if isinstance(x, AndOp):
#            counts["AND"] += 1
#            log.info(f"Counted AndOp, count: {counts}")
#            walk(x.a)
#            walk(x.b)
#        elif isinstance(x, OrOp):
#            counts["OR"] += 1
#            log.info(f"Counted OrOp, count: {counts}")
#            walk(x.a)
#            walk(x.a)
#            walk(x.b)
#        elif isinstance(x, XorOp):
#            counts["XOR"] += 1
#            log.info(f"Counted XorOp, count: {counts}")
#            walk(x.a)
#            walk(x.b)
#        elif isinstance(x, NotOp):
#            counts["NOT"] += 1
#            log.info(f"Counted NotOp, count: {counts}")
#            o = _unary_operand(x)
#            if o is not None: walk(o)
#        else:
#            log.info(f"Hit unexpected op!: op: {x} type: {type(x).__name__}")
#            # leaf-ish (BitSelect, Id, Const, etc.)
#            pass
#    log.info("Walking default path")
#    walk(n)
#    return counts

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
    for attr in ("var", "vector", "target", "expr", "base", "index"):
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

    if not isinstance(n, EqOp):
        return (None, None, False)
    lhs, rhs = n.lhs, n.rhs
    log.info(f"  LHS: {lhs} ({type(lhs)})")
    log.info(f"  RHS: {rhs} ({type(rhs)})")


    if isinstance(lhs, BitSelect) and isinstance(rhs, LogicConst):
        log.info("  → lhs is BitSelect and rhs is Const")
        base = _bit_base(lhs)
        index = _bit_index(lhs)
        log.info(f"    base: {base} (type: {type(base)})")
        log.info(f"    index: {index}")
        if isinstance(base, LogicVar):
            log.info(f"    base.name: {base.name}")
            return (base.name, index.value, is_pos)
    # Fallback: not a literal signal
    return (None, None, is_pos)


def _flatten_and(n):
    """Flatten a left-nested chain of AndOp into a list of leaf terms."""
    if isinstance(n, AndOp):
        return _flatten_and(n.left) + _flatten_and(n.right)
    return [n]

def parse_bitstring_literal(s: str) -> list[bool]:
    """Parses a Verilog-style bitstring like '4\'b1001' into [True, False, False, True]."""
    if "'" not in s:
        raise ValueError(f"Unsupported literal format: {s}")
    width, base_and_value = s.split("'")
    base = base_and_value[0].lower()
    value = base_and_value[1:]
    if base != "b":
        raise ValueError(f"Only binary constants are supported, got: {s}")
    return [c == "1" for c in value.zfill(int(width))]

def literal_bit_comparisons(tree: LogicTreeNode, target_signal: str | None = None) -> set[tuple[str | int, bool]]:
    """Returns set of (signal or bit index, polarity) pairs from equality comparisons to constants."""
    comparisons = set()

    def _walk(node):
        if isinstance(node, EqOp):
            lhs, rhs = node.lhs, node.rhs

            if isinstance(rhs, LogicConst):
                const_val = rhs.value

                # Convert to bits
                if isinstance(lhs, LogicVar):
                    bits = [bool(const_val)]
                    if target_signal is None or lhs.name == target_signal:
                        comparisons.add((lhs.name, bits[0]))

                elif isinstance(lhs, BitSelect):
                    bits = [bool(const_val)]
                    if isinstance(lhs.base, LogicVar):
                        if target_signal is None or lhs.base.name == target_signal:
                            comparisons.add((lhs.index.value, bits[0]))

                elif isinstance(lhs, Concat):
                    width = len(lhs.parts)
                
                    # Parse string bit literal like "2'b10" → [True, False]
                    if isinstance(const_val, str):
                        bits = parse_bitstring_literal(const_val)
                    elif isinstance(const_val, int):
                        bits = [(const_val >> i) & 1 == 1 for i in reversed(range(width))]
                    else:
                        raise TypeError(f"Unsupported constant type: {type(const_val)}")
                
                    if len(bits) != len(lhs.parts):
                        raise ValueError("Concat operand count doesn't match constant width")
                
                    for part, bit in zip(lhs.parts, bits):
                        if isinstance(part, LogicVar):
                            if target_signal is None or part.name == target_signal:
                                comparisons.add((part.name, bit))
                        elif isinstance(part, BitSelect):
                            if target_signal is None or part.var.name == target_signal:
                                comparisons.add((part.index.value, bit))

        for child in node.children:
            _walk(child)

    _walk(tree)
    return comparisons


def literal_sig_set(expr, target_signal: str) -> set[str]:
    """
    Returns a set of stringified bit selects like "s[1]", "s[0]" for all
    BitSelect nodes on the given signal name used in EqOps within an AndOp tree.
    Useful for matching signal bit positions regardless of polarity.
    """
    return {f"{target_signal}[{index}]" for index, _ in literal_bit_comparisons(expr, target_signal)}
#def literal_sig_set(n, only_name=None):
#    """
#    Collect a set of literal signals seen in a conjunction.
#
#    If `only_name` is set, only signals matching that name are included.
#    Returns:
#        - (name, is_pos) for scalar vars
#        - (name[idx], is_pos) for bit selects
#    This is optimized for readability. For index-based analysis, see `literal_bit_comparisons()`.
#    """
#    out = set()
#    for t in _flatten_and(n):
#        log.info(f"Clause: t: {t}")
#        log.info(f"Match: _literal_sig(t): {_literal_sig(t)}")
#        name, idx, is_pos = _literal_sig(t)
#        if name is None:
#            continue
#        if only_name is None or name == only_name:
#            if idx is None:
#                out.add((name, is_pos))
#            else:
#                out.add((f"{name}[{idx}]", is_pos))
#    return out
#
#def literal_bit_comparisons(n, signal_name: str):
#    """
#    Return set of (bit_index, value) pairs for comparisons like s[i] == 0 or s[i] == 1.
#    Only returns matches for the given signal_name.
#    """
#    out = set()
#    for t in _flatten_and(n):
#        name, idx, is_pos = _literal_sig(t)
#        if name == signal_name and idx is not None:
#            out.add((idx, is_pos))
#    return out
