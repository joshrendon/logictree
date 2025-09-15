
from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect


def logic_tree_to_ascii(tree, indent: int = 0) -> str:
    ind = ' ' * indent
    if tree is None:
        return ind + "None"

    # Const or Var
    if isinstance(tree, (LogicConst, LogicVar)):
        return ind + str(tree)

    # Assignment wrapper
    if isinstance(tree, LogicAssign):
        return f"{ind}Assign:\n{logic_tree_to_ascii(tree.rhs, indent + 2)}"

    # BitSelect
    if isinstance(tree, BitSelect):
        return f"{ind}BitSelect({tree.base}[{tree.index}])"

    # PartSelect
    if isinstance(tree, PartSelect):
        return f"{ind}PartSelect({tree.base}[{tree.msb}:{tree.lsb}])"

    # Concat
    if isinstance(tree, Concat):
        lines = [f"{ind}Concat"]
        for i, part in enumerate(tree.parts):
            lines.append(logic_tree_to_ascii(part, indent + 2))
        return "\n".join(lines)

    # LogicMux
    if isinstance(tree, LogicMux):
        lines = [f"{ind}MUX:"]
        lines.append(f"{ind} cond:\n{logic_tree_to_ascii(tree.selector, indent + 4)}")
        lines.append(f"{ind} if_true:\n{logic_tree_to_ascii(tree.if_true, indent + 4)}")
        lines.append(f"{ind} if_false:\n{logic_tree_to_ascii(tree.if_false, indent + 4)}")
        return "\n".join(lines)

    # IfStatement (before muxified)
    if isinstance(tree, IfStatement):
        lines = [f"{ind}IF:"]
        lines.append(f"{ind} condition:\n{logic_tree_to_ascii(tree.cond, indent + 2)}")
        lines.append(f"{ind} then_branch:\n{logic_tree_to_ascii(tree.then_branch, indent + 2)}")
        lines.append(f"{ind} else_branch:\n{logic_tree_to_ascii(tree.else_branch, indent + 2)}")
        return "\n".join(lines)

    # LogicOp (generic n-ary op)
    if isinstance(tree, LogicOp):
        lines = [f"{ind}{tree.label()}"]
        for operand in tree.operands:
            lines.append(logic_tree_to_ascii(operand, indent + 2))
        return "\n".join(lines)

    # Fallback
    return f"{ind}UNKNOWN<{type(tree).__name__}>: {str(tree)}"


def to_ascii(tree, indent=0):
    pad = "  " * indent
    if isinstance(tree, LogicOp):
        lines = [pad + tree.op]
        for child in tree.children:
            lines.append(to_ascii(child, indent + 1))
        return "\n".join(lines)
    elif isinstance(tree, LogicVar):
        return pad + f"{tree.name}"
    elif isinstance(tree, LogicConst):
        return pad + ("TRUE" if tree.value else "FALSE")
    else:
        return pad + str(tree)
