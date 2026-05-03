from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.types.base import TypedValue
from .exceptions import ContextIsolationError

# Stable int identity for a graph or node object within one execution run
GraphID = int
NodeID = int


@dataclass
class ExecutionContext:
    """
    Isolated per-graph execution sandbox.
    No shared mutable state between contexts.
    No persistence across executions.
    Enforces single-pass: a node may be stored exactly once.
    """
    graph: CDLGraph
    _node_values: Dict[NodeID, TypedValue] = field(default_factory=dict, repr=False)

    def store(self, node_id: NodeID, value: TypedValue) -> None:
        if node_id in self._node_values:
            raise ContextIsolationError(
                f"Node {node_id} already evaluated — single-pass violation"
            )
        self._node_values[node_id] = value

    def get(self, node_id: NodeID) -> Optional[TypedValue]:
        return self._node_values.get(node_id)

    def is_resolved(self, node_id: NodeID) -> bool:
        return node_id in self._node_values

    def all_outputs(self) -> Dict[NodeID, TypedValue]:
        return dict(self._node_values)


def make_context(graph: CDLGraph) -> ExecutionContext:
    """Create a fresh, empty execution context for a graph. No state is shared."""
    return ExecutionContext(graph=graph)
