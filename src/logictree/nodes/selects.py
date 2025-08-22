# in logictree/nodes/selects.py
class BitSelect:
    def __init__(self, base, index): self.base, self.index = base, index
    def __repr__(self): return f"{self.base}[{self.index}]"
    def default_label(self): return str(self)
    def set_viz_label(self, label): self._viz_label = label

class PartSelect:
    def __init__(self, base, msb, lsb): self.base, self.msb, self.lsb = base, msb, lsb
    def __repr__(self): return f"{self.base}[{self.msb}:{self.lsb}]"
    def default_label(self): return str(self)
    def set_viz_label(self, label): self._viz_label = label

class Concat:
    def __init__(self, parts): self.parts = parts
    def __repr__(self): return "{" + ", ".join(map(str, self.parts)) + "}"
    def default_label(self): return str(self)
    def set_viz_label(self, label): self._viz_label = label
