from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from .exceptions import ResolutionError


@dataclass
class ResolvedExecutionOrder:
    """
    Topologically sorted node list for a single CDLGraph.
    Leaf nodes appear before the nodes that consume them.
    Order is deterministic: DFS with operator-name tie-breaking.
    """
    nodes: List[CDLNode]


def resolve_order(graph: CDLGraph) -> ResolvedExecutionOrder:
    """
    Compute the single-pass execution order for a CDLGraph.
    - Topological sort only — no dynamic graph modification
    - Assumes DAG integrity guaranteed by CAS + MECP upstream
    - Raises ResolutionError on cycle detection
    """
    if not graph.nodes:
        raise ResolutionError("Cannot resolve execution order for empty graph")

    visited: Set[int] = set()
    in_stack: Set[int] = set()   # cycle detection
    order: List[CDLNode] = []

    def visit(node: CDLNode) -> None:
        nid = id(node)
        if nid in in_stack:
            raise ResolutionError(
                f"Cycle detected at operator '{node.operator.name}' — graph is not a DAG"
            )
        if nid in visited:
            return
        in_stack.add(nid)
        for inp in sorted(node.inputs, key=lambda n: n.operator.name):
            visit(inp)
        in_stack.discard(nid)
        visited.add(nid)
        order.append(node)

    for node in sorted(graph.nodes, key=lambda n: n.operator.name):
        visit(node)

    return ResolvedExecutionOrder(nodes=order)
