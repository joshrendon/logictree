class LogicTreeNode:
    def simplify(self):
        return self  # Default is no-op; override in subclasses

    def __str__(self):
        return self.__class__.__name__

    def depth(self):
        raise NotImplementedError

    def inputs(self) -> set[str]:
        return self.collect_input_names()
        #raise NotImplementedError

    def to_verilog(self):
        raise NotImplementedError

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError

    def contains_hole(self):
        return False
    
    def collect_input_names(self) -> set["LogicVar"]:
        return NotImplementedError("Subclasses should implement collect_inputs")

