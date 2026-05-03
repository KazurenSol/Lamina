from __future__ import annotations

from typing import Dict, List, Optional

from l_cdea.core.types.base import SemanticType
from .node import DiscourseNode, BASE_SALIENCE, make_node_id
from .edge import DiscourseEdge
from .state import DiscourseState
from .exceptions import MemoryGraphError


def add_node(state: DiscourseState, node: DiscourseNode) -> bool:
    """
    Add node to state. Returns True if added, False if already present.
    Caller is responsible for reinforcement if already present.
    """
    if node.id in state.nodes:
        return False
    state.nodes[node.id] = node
    state.salience_index[node.id] = node.salience
    return True


def add_edge(state: DiscourseState, edge: DiscourseEdge) -> bool:
    """
    Add edge if no identical (source, target, relation_type) triple exists.
    If a duplicate triple is found, merge provenance from the new edge into the
    existing one without creating a new edge. Returns True if added, False if merged.
    """
    for existing in state.edges:
        if (existing.source_id == edge.source_id
                and existing.target_id == edge.target_id
                and existing.relation_type == edge.relation_type):
            # Merge new provenance entries not already present (dedup by trace_id).
            existing_ids = {p.trace_id for p in (existing.provenance or ())}
            new_provs = tuple(
                p for p in (edge.provenance or ()) if p.trace_id not in existing_ids
            )
            if new_provs:
                existing.provenance = (existing.provenance or ()) + new_provs
            return False
    state.edges.append(edge)
    return True


def get_node(state: DiscourseState, node_id: str) -> Optional[DiscourseNode]:
    return state.nodes.get(node_id)


def get_nodes_by_type(state: DiscourseState, semantic_type: SemanticType) -> List[DiscourseNode]:
    return [n for n in state.nodes.values() if n.semantic_type == semantic_type]


def get_edges_by_relation(state: DiscourseState, relation_type: str) -> List[DiscourseEdge]:
    return [e for e in state.edges if e.relation_type == relation_type]


def get_edges_from(state: DiscourseState, source_id: str) -> List[DiscourseEdge]:
    return [e for e in state.edges if e.source_id == source_id]


def merge_duplicate(state: DiscourseState, node_id: str, reinforcement: float) -> None:
    """
    Duplicate merge rule: reinforce salience of existing node instead of creating a new one.
    Temporal reference is updated. Semantic content is not changed.
    """
    if node_id not in state.nodes:
        raise MemoryGraphError(f"Cannot merge: node '{node_id}' not found")
    state.nodes[node_id].salience += reinforcement
    state.nodes[node_id].updated_at = state.temporal_index
    state.salience_index[node_id] = state.nodes[node_id].salience


def lookup_by_value(state: DiscourseState, value: object) -> Optional[DiscourseNode]:
    for node in state.nodes.values():
        if node.value == value:
            return node
    return None
