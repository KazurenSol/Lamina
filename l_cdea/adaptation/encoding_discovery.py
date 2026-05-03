"""
Discover repeated structural patterns in CDL graphs that could be encoded more efficiently.
Candidate encodings are proposed, never auto-registered.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List

from l_cdea.normalization.canonicalizer.signature import compute_signature
from l_cdea.core.cdl.graph import CDLGraph


@dataclass
class EncodingCandidate:
    pattern_signature: str
    frequency: int
    estimated_compression_ratio: float
    description: str


def discover_encodings(graphs: List[CDLGraph], min_frequency: int = 3) -> List[EncodingCandidate]:
    """Find operator patterns that appear at least min_frequency times."""
    sig_counts: Counter = Counter()
    sig_descriptions: dict[str, str] = {}

    for g in graphs:
        sig = compute_signature(g)
        sig_key = str(sig)
        sig_counts[sig_key] += 1
        if sig_key not in sig_descriptions:
            sig_descriptions[sig_key] = f"graph with {len(g.nodes)} nodes"

    candidates = []
    for sig_key, freq in sig_counts.items():
        if freq >= min_frequency:
            ratio = 1.0 - (1.0 / freq)
            candidates.append(EncodingCandidate(
                pattern_signature=sig_key,
                frequency=freq,
                estimated_compression_ratio=ratio,
                description=sig_descriptions[sig_key],
            ))

    return sorted(candidates, key=lambda c: c.frequency, reverse=True)
