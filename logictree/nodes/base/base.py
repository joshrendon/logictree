import copy
import logging
from dataclasses import replace, field
from logictree.utils import overlay

log = logging.getLogger(__name__)

class LogicTreeNode:
    metadata: dict = field(default_factory=dict, compare=False, repr=False)

    def __setattr__(self, name, value):
        if name == "free_vars" and not callable(value):
            raise AttributeError("Do not assign to 'free_vars'; use '_free_vars' for caches.")
        super().__setattr__(name, value)

    def set_viz_label(self, text):
        overlay.set_viz_label(self, text)
        return self
    
    ##TODO: remove this monkey patch and return label() to the commented method below
    #@property
    #def label(self):
    #    raise RuntimeError("Direct .label access! Use .label() instead.")
    def label(self) -> str:
        viz = overlay.get_viz_label(self)
        if viz is not None:
            return viz
        # sensible fallbacks: LogicVar has .name, LogicConst has .value, else class name
        if hasattr(self, "name"):
            return getattr(self, "name")
        if hasattr(self, "value"):
            return str(getattr(self, "value"))
        return self.__class__.__name__

    def set_expr_source(self, text):
        overlay.set_expr_source(self, text)
        return self
 
    def get_expr_source(self):
        return overlay.get_expr_source(self)
    
    def cache_metrics(self, **kvs):
        overlay.cache_metrics(self, **kvs)

    def get_metric(self, key, default=None):
        return overlay.get_metric(self, key, default)

    def free_vars(self) -> set[str]:
        # Subclasses should override; if you keep a cache, return set(self._free_vars)
        return set()

    def clone_with_children(self, new_children):
        new = replace(self, children=tuple(new_children))  # or appropriate fields
        # Make metadata a shallow copy so edits on one don’t leak to the other
        object.__setattr__(new, "metadata", dict(self.metadata))
        return new

    def __str__(self):
        return self.label()

    def default_label(self):
        return self.__class__.__name__

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    @property
    def expr_source(self):
        return self.get_expr_source()

    @property
    def viz_label(self):
        return overlay.get_viz_label(self)

    @property
    def depth(self):
        raise NotImplementedError

    def inputs(self) -> set[str]:
        return []

    def to_verilog(self):
        raise NotImplementedError

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError

    def contains_hole(self):
        return False
    
    #def collect_input_names(self) -> set["LogicVar"]:
    #    return NotImplementedError("Subclasses should implement collect_inputs")

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

    def simplify(self):
        raise NotImplementedError("Use `simplify_logic_tree(node)` instead.")
