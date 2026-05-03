from __future__ import annotations

from typing import Dict, List

from l_cdea.core.cdl.graph import CDLGraph
from .signature import CanonicalSignature, compute_signature
from .exceptions import EquivalenceDetectionError


def are_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    """
    Two graphs are equivalent iff their canonical signatures are identical.
    Structural equivalence only — not semantic equality.
    """
    try:
        return compute_signature(g1) == compute_signature(g2)
    except Exception as e:
        raise EquivalenceDetectionError(f"Equivalence check failed: {e}") from e


def group_by_equivalence(graphs: List[CDLGraph]) -> Dict[CanonicalSignature, List[CDLGraph]]:
    """
    Partition graphs into equivalence classes keyed by CanonicalSignature.
    All original graphs are preserved — none deleted, only grouped.
    """
    if not graphs:
        raise EquivalenceDetectionError("Cannot compute equivalence classes from empty graph list")

    classes: Dict[CanonicalSignature, List[CDLGraph]] = {}
    for graph in graphs:
        sig = compute_signature(graph)
        classes.setdefault(sig, []).append(graph)
    return classes
