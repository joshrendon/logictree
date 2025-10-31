
from abc import ABC, abstractmethod


class StructuralOp(ABC):
    """ Interface for non-primitive nodes with undefined timing semantics."""
    def depth(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a structural node; "
            "depth undefined until lowered."
        )

    def delay(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a structural node; "
            "delay undefined until lowered."
        )

    @abstractmethod
    def label(self): ...

    @abstractmethod
    def to_json_dict(self): ...
