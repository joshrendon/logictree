# logictree/utils/gate_factory.py
def create_gate(op_name, lhs, rhs):
    if op_name == "AND":
        from logictree.nodes.ops.gates import AndOp

        return AndOp(lhs, rhs)
    elif op_name == "OR":
        from logictree.nodes.ops.gates import OrOp

        return OrOp(lhs, rhs)
    elif op_name == "XOR":
        from logictree.nodes.ops.gates import XorOp

        return XorOp(lhs, rhs)
    elif op_name == "NAND":
        from logictree.nodes.ops.gates import NandOp

        return NandOp(lhs, rhs)
    elif op_name == "NOR":
        from logictree.nodes.ops.gates import NorOp

        return NorOp(lhs, rhs)
    elif op_name == "XNOR":
        from logictree.nodes.ops.gates import XnorOp

        return XnorOp(lhs, rhs)
    else:
        raise ValueError(f"Unknown op_name '{op_name}'")
