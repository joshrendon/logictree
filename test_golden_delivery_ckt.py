from logictree.nodes.ops import AndOp, LogicVar

# Define variables
C = LogicVar("customs_cleared")
T = LogicVar("transit_ready")
A = LogicVar("arrived_on_truck")

# Build tree
S = AndOp(C, T)        # shipment_released
D = AndOp(S, A)        # delivery_confirmed

cloned = D.clone()
simplified = cloned.simplify()
print("Original Tree:")
print(D)
print("Simplified Tree:")
print(simplfied)
