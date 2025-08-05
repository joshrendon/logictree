import copy
import logging
log = logging.getLogger(__name__)

class LogicTreeNode:
    def __init__(self):
        self._viz_label = None # Vizualization field
    
    def set_viz_label(self, label: str):
        self._viz_label = label
        return self

    def simplify(self):
        return self  # Default is no-op; override in subclasses

    def __str__(self):
        return self.__class__.__name__

    def label(self):
        if self._viz_label is not None:
            log.debug(f"[label] using _viz_label: {self._viz_label}")
            return self._viz_label
        lbl = self.default_label()
        log.debug(f"[label] using default label: {lbl}")
        return lbl

    def default_label(self):
        return self.__class__.__name__

    @property
    def depth(self):
        raise NotImplementedError

    def inputs(self) -> set[str]:
        return self.collect_input_names()

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
        log.debug(f"Base to_json_dict called on type={type(self).__name__}")
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

    def flatten(self):
        return self.simplify()

