from dataclasses import dataclass
from typing import Dict, List

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.compiler import CompiledOutput
from .signature import CanonicalSignature, compute_signature
from .equivalence import are_equivalent, group_by_equivalence
from .normalize import NormalizedCDLGraph, normalize
from .merge import CanonicalGraphSet, merge
from .exceptions import CanonicalizationError, EquivalenceDetectionError, NormalizationError


@dataclass
class CanonicalizationResult:
    """Output contract of the canonicalizer. Passed directly to MECP."""
    canonical_graphs: CanonicalGraphSet
    signatures: List[CanonicalSignature]
    equivalence_map: Dict[CanonicalSignature, List[CDLGraph]]


def canonicalize(compiled: CompiledOutput) -> CanonicalizationResult:
    """
    Normalize and partition the over-generated graph set from the compiler.
    Pipeline: normalize each graph → merge by signature → expose equivalence map.
    Pure function — no mutation, no MECP, no DiscourseState.
    """
    normalized = [normalize(g) for g in compiled.graphs]
    canonical_set = merge(normalized)

    return CanonicalizationResult(
        canonical_graphs=canonical_set,
        signatures=list(canonical_set.equivalence_classes.keys()),
        equivalence_map=canonical_set.equivalence_classes,
    )


__all__ = [
    "canonicalize",
    "CanonicalizationResult",
    "CanonicalGraphSet",
    "CanonicalSignature",
    "NormalizedCDLGraph",
    "are_equivalent",
    "compute_signature",
    "CanonicalizationError",
    "EquivalenceDetectionError",
    "NormalizationError",
]
