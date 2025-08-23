from ..base.base import LogicTreeNode


class LogicHole(LogicTreeNode):
    def __init__(self, name: str="UNSPECIFIED"):
        super().__init__()
        self.name = name

    @property
    def children(self):
        return  []

    def equals(self, other):
        return isinstance(other, LogicHole) and self.name == other.name

    def simplify(self):
        return self

    def __str__(self):
        return self.name

    def inputs(self) -> set[str]:
        return self.collect_input_names()

    def depth(self):
        return 0

    def to_verilog(self):
        return f"/* {self.name} */"

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        my_id = next_id[0]
        next_id[0] += 1
        graph.append(f'  node{my_id} [label="Hole\\n{self.name}", shape=octagon, style=dashed];')
        if parent_id is not None:
            graph.append(f'  node{parent_id} -> node{my_id};')
        return my_id

    def contains_hole(self):
        return True

    def __repr__(self):
        return f"LogicHole({self.name})"

    def collect_input_names(self) -> set[str]:
        return {self.name}
