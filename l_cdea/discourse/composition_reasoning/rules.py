"""
Composition rules for COMPOSE_RELATIONSHIPS.

V1 rules:
  Rule 1 — indirect: path length >= 2 → indirectly_depends_on target.
  Rule 2 — direct vs indirect separation: depth 1 = direct, depth >= 2 = indirect.
  Rule 3 — deduplication: multiple paths to same target → one ComposedRelationship.
  Rule 4 — dominance: target reachable directly AND indirectly → direct wins, drop from indirect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from l_cdea.discourse.provenance.model import Provenance
from l_cdea.discourse.multi_hop_reasoning.traversal import (
    RelationshipClosureResult,
    RelationshipPath,
)


@dataclass(frozen=True)
class ComposedRelationship:
    source: str
    relation_type: str
    target: str
    is_indirect: bool
    paths: Tuple[Tuple[str, ...], ...]    # one tuple per traversal path
    provenance: Tuple[Provenance, ...]    # deduplicated, sorted by confidence DESC


@dataclass(frozen=True)
class CompositionResult:
    source_term: str
    relation_type: str
    direct: Tuple[ComposedRelationship, ...]
    indirect: Tuple[ComposedRelationship, ...]
    fallback_used: bool


def apply_rules(closure_result: RelationshipClosureResult) -> CompositionResult:
    """Apply V1 composition rules to produce direct/indirect separation."""
    direct_by_target: Dict[str, List[RelationshipPath]] = {}
    indirect_by_target: Dict[str, List[RelationshipPath]] = {}

    for path in closure_result.paths:
        if path.depth == 1:
            direct_by_target.setdefault(path.target, []).append(path)
        else:
            indirect_by_target.setdefault(path.target, []).append(path)

    # Rule 4 — dominance: remove from indirect any target that is also direct
    for target in list(direct_by_target):
        indirect_by_target.pop(target, None)

    def _merge(target: str, paths_list: List[RelationshipPath], is_indirect: bool) -> ComposedRelationship:
        seen_ids: set = set()
        merged: List[Provenance] = []
        for p in paths_list:
            for prov in p.provenance:
                if prov.trace_id not in seen_ids:
                    seen_ids.add(prov.trace_id)
                    merged.append(prov)
        merged.sort(key=lambda pv: -pv.confidence)
        return ComposedRelationship(
            source=closure_result.source_term,
            relation_type=closure_result.relation_type,
            target=target,
            is_indirect=is_indirect,
            paths=tuple(p.path for p in paths_list),
            provenance=tuple(merged),
        )

    direct = tuple(
        _merge(t, paths, False)
        for t, paths in sorted(direct_by_target.items())
    )
    indirect = tuple(
        _merge(t, paths, True)
        for t, paths in sorted(indirect_by_target.items())
    )

    return CompositionResult(
        source_term=closure_result.source_term,
        relation_type=closure_result.relation_type,
        direct=direct,
        indirect=indirect,
        fallback_used=(len(direct) == 0 and len(indirect) == 0),
    )
