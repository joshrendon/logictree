from logictree.nodes.control.assign import LogicAssign
from logictree.nodes.control.case import CaseItem, CaseStatement
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.ops.gates import AndOp, NandOp, NotOp, OrOp, XnorOp, XorOp
from logictree.nodes.ops.mux import LogicMux
from logictree.nodes.ops.ops import LogicConst, LogicOp, LogicVar
from logictree.nodes.selects import BitSelect, Concat, PartSelect
from logictree.nodes.struct.module import Module


def all_node_classes():
    return [
        LogicVar,
        LogicConst,
        LogicOp,
        AndOp,
        OrOp,
        NotOp,
        XorOp,
        XnorOp,
        NandOp,
        LogicAssign,
        CaseStatement,
        CaseItem,
        IfStatement,
        LogicMux,
        Module,
        BitSelect,
        PartSelect,
        Concat,
    ]
