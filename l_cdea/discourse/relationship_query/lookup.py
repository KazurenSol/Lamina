"""
lookup_relationships(term, relation_type, state) → (RelationshipLookupResult, RelationshipQueryTrace)

Steps:
1. Normalize term.
2. Find source node whose value matches the normalized term.
3. Find outgoing edges with the given relation_type.
4. Collect RelationshipResult per edge (includes per-edge provenance).
5. Sort deterministically: edge salience DESC, provenance confidence DESC, value ASC.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from l_cdea.discourse.provenance.model import Provenance
from l_cdea.discourse.state import DiscourseState
from l_cdea.discourse.relationship_query.normalization import normalize_term
from l_cdea.discourse.relationship_query.trace import RelationshipQueryTrace


@dataclass(frozen=True)
class RelationshipResult:
    """A single resolved relationship edge with its provenance."""
    target_value: str
    relation_type: str
    source_term: str
    edge_id: Optional[str]              # "source_id → target_id"
    provenance: Tuple[Provenance, ...]


@dataclass(frozen=True)
class RelationshipLookupResult:
    hit: bool
    term: str
    normalized_term: str
    relation_type: str
    values: Tuple[str, ...]              # target term values, sorted (backward compat)
    results: Tuple[RelationshipResult, ...]  # richer per-edge results with provenance
    source_node_id: Optional[str]
    matched_edge_ids: Tuple[str, ...]    # "src_id → tgt_id" strings
    provenance_count: int


def lookup_relationships(
    term: str,
    relation_type: str,
    state: DiscourseState,
) -> Tuple[RelationshipLookupResult, RelationshipQueryTrace]:
    norm_term = normalize_term(term)

    # Find source node whose normalized value matches
    source_node = None
    for node in state.nodes.values():
        node_norm = normalize_term(str(node.value))
        if node_norm == norm_term:
            source_node = node
            break

    if source_node is None:
        result = _miss(term, norm_term, relation_type, source_node_id=None)
        trace = _trace_miss(term, norm_term, relation_type, source_node_id=None)
        return result, trace

    # Find outgoing edges with matching relation_type
    matching_edges = [
        e for e in state.edges
        if e.source_id == source_node.id and e.relation_type == relation_type
    ]

    if not matching_edges:
        result = _miss(term, norm_term, relation_type, source_node_id=source_node.id)
        trace = _trace_miss(term, norm_term, relation_type, source_node_id=source_node.id)
        return result, trace

    # Build RelationshipResult per edge, then sort
    candidates: List[Tuple[float, float, str, RelationshipResult]] = []
    total_prov = 0

    for edge in matching_edges:
        target_node = state.nodes.get(edge.target_id)
        if target_node is None:
            continue
        prov = tuple(edge.provenance or ())
        max_conf = max((p.confidence for p in prov), default=0.0)
        total_prov += len(prov)
        edge_id = f"{edge.source_id} → {edge.target_id}"
        rel_result = RelationshipResult(
            target_value=str(target_node.value),
            relation_type=relation_type,
            source_term=norm_term,
            edge_id=edge_id,
            provenance=prov,
        )
        candidates.append((edge.salience, max_conf, str(target_node.value), rel_result))

    # Sort: salience DESC, confidence DESC, value ASC
    candidates.sort(key=lambda x: (-x[0], -x[1], x[2]))

    results = tuple(c[3] for c in candidates)
    values = tuple(c[2] for c in candidates)
    edge_ids = tuple(c[3].edge_id for c in candidates if c[3].edge_id)

    lookup_result = RelationshipLookupResult(
        hit=True,
        term=term,
        normalized_term=norm_term,
        relation_type=relation_type,
        values=values,
        results=results,
        source_node_id=source_node.id,
        matched_edge_ids=edge_ids,
        provenance_count=total_prov,
    )

    edge_dicts = [_edge_dict(r) for r in results]
    trace = RelationshipQueryTrace(
        term=term,
        normalized_term=norm_term,
        relation_type=relation_type,
        matched_source_node_id=source_node.id,
        matched_edges=edge_dicts,
        returned_values=list(values),
        hit=True,
        fallback_used=False,
    )
    return lookup_result, trace


# ── Internal helpers ──────────────────────────────────────────────────────────

def _miss(
    term: str,
    norm_term: str,
    relation_type: str,
    source_node_id: Optional[str],
) -> RelationshipLookupResult:
    return RelationshipLookupResult(
        hit=False,
        term=term,
        normalized_term=norm_term,
        relation_type=relation_type,
        values=(),
        results=(),
        source_node_id=source_node_id,
        matched_edge_ids=(),
        provenance_count=0,
    )


def _trace_miss(
    term: str,
    norm_term: str,
    relation_type: str,
    source_node_id: Optional[str],
) -> RelationshipQueryTrace:
    return RelationshipQueryTrace(
        term=term,
        normalized_term=norm_term,
        relation_type=relation_type,
        matched_source_node_id=source_node_id,
        matched_edges=[],
        returned_values=[],
        hit=False,
        fallback_used=True,
    )


def _edge_dict(r: RelationshipResult) -> Dict:
    from l_cdea.discourse.provenance.model import provenance_to_dict
    return {
        "target_value": r.target_value,
        "relation_type": r.relation_type,
        "edge_id": r.edge_id,
        "provenance_count": len(r.provenance),
        "provenance_entries": [provenance_to_dict(p) for p in r.provenance],
    }
