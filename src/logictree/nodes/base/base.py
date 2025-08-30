import copy
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LogicTreeNode:

    @property
    def depth(self) -> int:
        clsname = self.__class__.__name__
        raise NotImplementedError(
            f".depth() not implemented for node of type {clsname}"
        )

    def __str__(self):
        return self.name if hasattr(self, "name") else self.__class__.__name__

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def free_vars(self) -> set[str]:
        """Override in subclasses"""
        return set()

    def inputs(self) -> list:
        return []

    def to_verilog(self):
        raise NotImplementedError

    def to_dot(self, graph, parent_id=None, next_id=[0]):
        raise NotImplementedError

    def to_json_dict(self):
        from logictree.utils.serialize import logic_tree_to_json

        log.debug(f"Base to_json_dict called on type={type(self).__name__}")
        return logic_tree_to_json(self)

    def clone(self):
        """Deep copy the node and clear any internal caches manually (if needed)."""
        clone = copy.deepcopy(self)
        # overlays are external now; we don't touch _depth, _delay, etc.
        return clone

    def simplify(self):
        raise NotImplementedError("Use `simplify_logic_tree(node)` instead.")

    def contains_hole(self):
        return False
