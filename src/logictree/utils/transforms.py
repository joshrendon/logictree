import logging

from logictree.nodes.control.assign import ProceduralAssign
from logictree.nodes.struct.statement import BlockStatement

log = logging.getLogger(__name__)

def unwrap_branch(branch):
    """Strip away trivial BlockStatement(ProceduralAssign) wrappers.

    If the branch is exactly a BlockStatement containing one ProceduralAssign
    to the same LHS as the outer assignment, return just the RHS.
    Otherwise return the branch as-is.
    """

    if isinstance(branch, BlockStatement):
        if (len(branch.statements) == 1
                and isinstance(branch.statements[0], ProceduralAssign)):
            return branch.statements[0].rhs
    return branch

def build_ite_chain(iteopchain):
    """Dummy shell for ite chain transformation builder util"""
