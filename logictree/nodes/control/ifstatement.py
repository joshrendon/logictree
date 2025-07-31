from ..base.base import LogicTreeNode
from typing import Dict, Tuple, Union, Optional, List

class FlattenedIfStatement(LogicTreeNode):
    def __init__(self, cond, then_branch, else_if_branches=None, else_branch=None):
        super().__init__()
        self.cond= cond
        self.then_branch = then_branch
        self.else_if_branches = else_if_branches or []
        self.else_branch = else_branch

        self.children = []
        if self.cond:
            self.children.append(self.cond)
        if self.then_branch:
            self.children.append(self.then_branch)
        if self.else_branch:
            self.children.append(self.else_branch)

    @property
    def label(self):
        return f"if({self.cond.label})"

    @property
    def depth(self):
        # Conservative depth: max depth across all branches
        all_branches = [self.then_branch] + [b for _, b in self.else_if_branches]
        if self.else_branch:
            all_branches.append(self.else_branch)
        return 1 + max((b.depth for b in all_branches), default=0)

    @property
    def delay(self):
        return 0 #TODO: Return a real value not just 0

class IfStatement(LogicTreeNode):
    def __init__(self, cond, then_branch, else_branch=None):
        super().__init__()
        self.cond = cond # Expression node
        self.then_branch = then_branch        # Could be assignment or block
        self.else_branch = else_branch        # Optional: either another IfStatement or block

        self.children = []
        #if self.cond:
        #    self.children.append(self.cond)
        #if self.then_branch:
        #    self.children.append(self.then_branch)
        #if self.else_branch:
        #    self.children.append(self.else_branch)

    #@property
    #def label(self):
    #    return f"if({self.cond})"
    def is_else_if(self) -> bool:
        # Used during rendering to decide if this should be labeled 'else if'
        return getattr(self, '_is_else_if', False)

    @property
    def label(self) -> str:
        label = f"{'else if' if self.is_else_if() else 'if'}({self.condition})"
        return label

    def children(self) -> List["LogicTreeNode"]:
        children = [self.condition, self.then_branch]
        if self.else_branch:
            if isinstance(self.else_branch, IfStatement):
                # Mark it as an else-if for UI rendering
                self.else_branch._is_else_if = True
                children.append(self.else_branch)
            else:
                children.append(self.else_branch)
        return children

    @property
    def depth(self) -> int:
        branches = [self.then_branch]
        if self.else_branch:
            branches.append(self.else_branch)
        return 1 + max([self.cond.depth] + [b.depth for b in branches])
    
    @property
    def delay(self) -> int:
        def safe_delay(node):
            if node is None:
                return 0
            d = getattr(node, "delay", None)
            return d if d is not None else 0

        branches = [self.then_branch]
        if self.else_branch:
            branches.append(self.else_branch)
        return 1 + max([safe_delay(self.cond.delay)] + [safe_delay(b.delay) for b in branches])
    #@property
    #def depth(self) -> int:
    #    return getattr(self.rhs, "depth", 0)

    #@property
    #def delay(self) ->int:
    #    # placeholder for future gate-delay modeling
    #    if hasattr(self, "annotated_delay"):
    #        return self.annotated_delay
    #    # Default to RHS delay
    #    return getattr(self.rhs, "delay", 0)

    def to_json_dict(self):
        return {
            "type": "IfStatement",
            "label": self.label,
            "expr_source": str(self.condition),
            "children": [
                {
                    "label": "then",
                    "type": "ThenBranch",
                    "children": [self.then_branch.to_json_dict()]
                }
            ] + (
                [{
                    "label": "else",
                    "type": "ElseBranch",
                    "children": [self.else_branch.to_json_dict()]
                }] if self.else_branch else []
            ),
            "depth": self.depth,
            "delay": self.delay
        }

    def simplify(self) -> "IfStatement":
        """
        Flattens nested `else_branch` IfStatements into a linear chain,
        only when they represent `else if` logic (i.e., else_branch is
        another IfStatement with no else).
        """
        simplified_then = self.then_branch.simplify() if hasattr(self.then_branch, "simplify") else self.then_branch
        simplified_else = self.else_branch.simplify() if hasattr(self.else_branch, "simplify") else self.else_branch
    
        # Flatten else-if chains into linear else_if_branches (for semantic clarity)
        else_if_branches = []
        current = simplified_else
    
        while isinstance(current, IfStatement) and current.else_branch is None:
            else_if_branches.append((current.condition, current.then_branch))
            current = None  # no further else_branch
    
        return FlattenedIfStatement(
            cond=self.cond,
            then_branch=simplified_then,
            else_if_branches=else_if_branches,
            else_branch=current
        )
    
