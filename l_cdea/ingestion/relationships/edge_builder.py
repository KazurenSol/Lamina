"""
build_edges(edges, discourse_state) → int

Converts RelationshipEdge objects into DiscourseNodes (for terms) and
DiscourseEdges, persisting both into the given DiscourseState.

Rules:
- Source and target term nodes are created if missing.
- Duplicate (source, relation, target) triples merge provenance; no new edge.
- Salience of new term nodes is 0.5 (lower than definition nodes at 1.0).
- Ordering is deterministic: edges processed in the order they arrive.
"""
from __future__ import annotations

from typing import List

from l_cdea.core.types.base import SemanticType
from l_cdea.discourse.edge import DiscourseEdge
from l_cdea.discourse.memory_graph import add_node, add_edge
from l_cdea.discourse.node import DiscourseNode, make_node_id
from l_cdea.discourse.state import DiscourseState
from l_cdea.ingestion.relationships.extractor import RelationshipEdge

_TERM_SALIENCE = 0.5


def build_edges(edges: List[RelationshipEdge], state: DiscourseState) -> int:
    """
    Write relationship edges (and implicit term nodes) into state.
    Returns the count of new DiscourseEdges added (excludes merged duplicates).
    """
    added = 0
    for rel_edge in edges:
        source_id = _ensure_term_node(rel_edge.source_term, state, rel_edge.provenance)
        target_id = _ensure_term_node(rel_edge.target_term, state, rel_edge.provenance)

        discourse_edge = DiscourseEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=rel_edge.relation_type,
            salience=rel_edge.confidence,
            provenance=(rel_edge.provenance,),
        )
        if add_edge(state, discourse_edge):
            added += 1

    return added


def _ensure_term_node(term: str, state: DiscourseState, provenance) -> str:
    """Return node_id for term, creating a minimal node if not already present."""
    node_id = make_node_id(SemanticType.ENTITY, term)
    if node_id not in state.nodes:
        node = DiscourseNode(
            id=node_id,
            semantic_type=SemanticType.ENTITY,
            value=term,
            salience=_TERM_SALIENCE,
            created_at=state.temporal_index,
            updated_at=state.temporal_index,
            provenance=(provenance,),
            metadata={"category": "relationship_term", "term": term},
        )
        add_node(state, node)
    return node_id
