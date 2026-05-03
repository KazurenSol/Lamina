from __future__ import annotations

from typing import Dict, List

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import CanonicalSignature
from .scheduler import ExecutionQueue, PriorityMap
from .exceptions import PruningError

ExecutionSubset = List[CDLGraph]


def prune(
    queue: ExecutionQueue,
    priority_map: PriorityMap,
    graph_to_sig: Dict[int, CanonicalSignature],
    threshold: float,
) -> ExecutionSubset:
    """
    Filter the ordered execution queue to the subset where Priority >= threshold.

    Hard guarantee: at least one graph is always returned (top-priority fallback)
    so the system invariant 'produce at least one execution path' is never violated.

    No semantic pruning — decisions are purely cost/benefit structural.
    """
    if not queue:
        raise PruningError("Cannot prune an empty execution queue")

    selected: ExecutionSubset = []
    for graph in queue:
        sig = graph_to_sig.get(id(graph))
        if sig is None:
            raise PruningError("Graph missing from signature map — canonicalization may be incomplete")
        priority = priority_map.get(sig, 0.0)
        if priority >= threshold:
            selected.append(graph)

    # Invariant: always return at least one graph (spec: §5 — must produce at least one path)
    if not selected:
        selected = [queue[0]]

    return selected


def build_graph_sig_map(
    equivalence_map: Dict[CanonicalSignature, List[CDLGraph]],
) -> Dict[int, CanonicalSignature]:
    """
    Build an id(graph) → CanonicalSignature lookup for use during pruning.
    Uses object identity (id) so no mutation or hashing of CDLGraph is needed.
    """
    mapping: Dict[int, CanonicalSignature] = {}
    for sig, graphs in equivalence_map.items():
        for graph in graphs:
            mapping[id(graph)] = sig
    return mapping
