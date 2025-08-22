import pytest
pytestmark = [pytest.mark.unit]

from logictree.nodes.ops import AndOp, LogicVar
from logictree.transforms.simplify import simplify_logic_tree

# Define variables
C = LogicVar("customs_cleared")
T = LogicVar("transit_ready")
A = LogicVar("arrived_on_truck")

# Build tree
S = AndOp(C, T)        # shipment_released
D = AndOp(S, A)        # delivery_confirmed

simplified = simplify_logic_tree(D)
print("Original Tree:")
print(D)
print("Simplified Tree:")
print(simplified)
