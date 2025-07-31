import copy
class LogicTreeNode:
    def simplify(self):
        return self  # Default is no-op; override in subclasses

    def __str__(self):
        return self.__class__.__name__

    @property
    def label(self):
        return self.__class__.__name__

    @property
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

    def to_json_dict(self):
        from logictree.utils.serialize import logic_tree_to_json
        # Fallback to generic serializer
        return logic_tree_to_json(self)

    def clone(self):
        import copy
        clone = copy.deepcopy(self)
        if hasattr(clone, "_depth"):
            clone._depth = None
        if hasattr(clone, "_delay"):
            clone._delay = None
        if hasattr(clone, "_cached_expr"):
            clone._cached_expr = None
        return clone

