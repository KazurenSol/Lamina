from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from l_cdea.core.cdl.graph import CDLGraph
from .signature import CanonicalSignature
from .normalize import NormalizedCDLGraph
from .exceptions import CanonicalizationError


@dataclass
class CanonicalGraphSet:
    """
    Partitioned semantic space keyed by canonical signature.
    Every original graph is preserved inside an equivalence class.
    No graph is deleted — information loss is forbidden.
    """
    equivalence_classes: Dict[CanonicalSignature, List[CDLGraph]] = field(default_factory=dict)

    @property
    def unique_count(self) -> int:
        return len(self.equivalence_classes)

    @property
    def total_count(self) -> int:
        return sum(len(v) for v in self.equivalence_classes.values())

    def all_graphs(self) -> List[CDLGraph]:
        """Return all original graphs across all equivalence classes."""
        result = []
        for graphs in self.equivalence_classes.values():
            result.extend(graphs)
        return result


def merge(normalized_graphs: List[NormalizedCDLGraph]) -> CanonicalGraphSet:
    """
    Collapse normalized graphs into equivalence classes by signature.
    Graphs with identical signatures are grouped — not deleted or merged into one.
    The full original graph set remains recoverable via equivalence_classes.values().
    """
    if not normalized_graphs:
        raise CanonicalizationError("Cannot merge empty normalized graph list")

    classes: Dict[CanonicalSignature, List[CDLGraph]] = {}
    for ng in normalized_graphs:
        classes.setdefault(ng.signature, []).append(ng.source)

    return CanonicalGraphSet(equivalence_classes=classes)
