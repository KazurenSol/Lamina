"""
Candidate algorithmic backends for CDL execution.
All candidates must be deterministic, type-safe, and pass benchmarks before registration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class AlgorithmCandidate:
    name: str
    version: str
    replaces: str           # name of operator or pipeline stage it targets
    implementation: Callable
    deterministic: bool
    description: str


def _topological_sort_kahn(nodes, edges):
    """Kahn's algorithm for topological sort — O(V+E)."""
    from collections import deque
    in_degree = {n: 0 for n in nodes}
    adj = {n: [] for n in nodes}
    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1
    queue = deque(n for n in nodes if in_degree[n] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(adj[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return order


ALGORITHM_CANDIDATES: List[AlgorithmCandidate] = [
    AlgorithmCandidate(
        name="kahn_topological_sort",
        version="1.0",
        replaces="cdl_graph._topological_order",
        implementation=_topological_sort_kahn,
        deterministic=True,
        description="Kahn's algorithm for deterministic topological ordering of CDL graphs.",
    ),
]
