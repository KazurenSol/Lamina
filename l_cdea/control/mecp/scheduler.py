from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import CanonicalSignature
from l_cdea.normalization.canonicalizer import CanonicalizationResult
from .cost_model import CostMap
from .scoring import GainMap
from .exceptions import SchedulingError

ExecutionQueue = List[CDLGraph]
PriorityMap = Dict[CanonicalSignature, float]


@dataclass(frozen=True)
class _ScoredEntry:
    graph: CDLGraph
    signature: CanonicalSignature
    priority: float
    # Stable string key used for deterministic tie-breaking without relying on id() or hash()
    tiebreak_key: str


def schedule(
    canonical: CanonicalizationResult,
    cost_map: CostMap,
    gain_map: GainMap,
) -> Tuple[ExecutionQueue, PriorityMap]:
    """
    Rank all graphs by Priority = InformationGain / Cost.
    Deterministic: sorted descending by priority, tie-broken by canonical structure string.
    Returns the ordered execution queue and a per-signature priority map.
    """
    if not canonical.equivalence_map:
        raise SchedulingError("Cannot schedule an empty canonical graph set")

    priority_map: PriorityMap = {}
    entries: List[_ScoredEntry] = []

    for sig, graphs in canonical.equivalence_map.items():
        cost = cost_map.get(sig, 0.0)
        gain = gain_map.get(sig, 0.0)

        # Guard against zero cost — treat as minimal positive to avoid division by zero
        priority = gain / cost if cost > 0.0 else gain
        priority_map[sig] = priority

        # Tiebreak key: string encoding of the canonical structure (session-stable)
        tiebreak = _sig_key(sig)

        for graph in graphs:
            entries.append(_ScoredEntry(
                graph=graph,
                signature=sig,
                priority=priority,
                tiebreak_key=tiebreak,
            ))

    # Sort descending by priority; ascending tiebreak key for determinism within same priority
    entries.sort(key=lambda e: (-e.priority, e.tiebreak_key))

    return [e.graph for e in entries], priority_map


def _sig_key(sig: CanonicalSignature) -> str:
    """Deterministic string representation of a signature for stable tie-breaking."""
    parts = []
    for ns in sig.nodes:
        parts.append(f"{ns.operator_name}:{ns.output_type}:{ns.input_indices}")
    return "|".join(parts)
