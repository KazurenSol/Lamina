from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set
from .node import CDLNode
from .exceptions import GraphExecutionError


@dataclass
class CDLGraph:
    """Directed acyclic semantic execution graph."""

    nodes: List[CDLNode] = field(default_factory=list)

    def add_node(self, node: CDLNode):
        self.nodes.append(node)

    def _topological_order(self) -> List[CDLNode]:
        """
        Returns nodes in dependency-first order.
        Required by the DETERMINISM CONTRACT: inputs must be resolved
        before any node that consumes them executes.
        """
        visited: Set[int] = set()
        order: List[CDLNode] = []

        def visit(node: CDLNode):
            if id(node) in visited:
                return
            visited.add(id(node))
            for inp in node.inputs:
                visit(inp)
            order.append(node)

        for node in self.nodes:
            visit(node)
        return order

    def execute(self) -> List[CDLNode]:
        """Deterministic graph execution (post-MECP phase)."""
        for node in self._topological_order():
            if not node.inputs:
                continue  # leaf node — value must be pre-set by compiler
            try:
                args = [inp.value for inp in node.inputs]
                node.value = node.operator.execute(*args)
            except Exception as e:
                raise GraphExecutionError(str(e)) from e

        return self.nodes
