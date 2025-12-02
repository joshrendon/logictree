import pytest

pytestmark = [pytest.mark.integration]

from logictree.nodes.control.assign import ProceduralAssign
from logictree.nodes.control.ifstatement import IfStatement
from logictree.nodes.struct.module import Module
from logictree.utils.transforms import build_ite_chain


def lower_procedural_assigns_to_signal_map(module: Module) -> None:
    for ab in module.always_blocks:
        assigns_by_lhs = {}
        for stmt in ab.body.statements:
            if isinstance(stmt, ProceduralAssign):
                assigns_by_lhs.setdefault(stmt.lhs.name, []).append(stmt)
            elif isinstance(stmt, IfStatement):
                # handle recursive lowering later
                pass

        for lhs, stmts in assigns_by_lhs.items():
            expr = build_ite_chain(stmts)  # helper to fold in order
            module.signal_map[lhs] = expr
