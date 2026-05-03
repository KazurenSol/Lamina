"""
compute_closure(term, relation_type, state, max_depth) → (RelationshipClosureResult, MultiHopTrace)

Breadth-first traversal over DiscourseState relationship edges.

Rules:
1. BFS from source node.
2. Traverse only edges matching relation_type.
3. Visited set prevents cycles and revisiting nodes.
4. max_depth bounds exploration depth (paths at exactly max_depth are included).
5. Paths sorted: depth ASC, target ASC, path-string ASC.
6. Provenance aggregated from all edges along each path.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from l_cdea.discourse.provenance.model import Provenance
from l_cdea.discourse.state import DiscourseState
from l_cdea.discourse.relationship_query.normalization import normalize_term
from l_cdea.discourse.multi_hop_reasoning.trace import MultiHopTrace, PathTrace

DEFAULT_MAX_DEPTH = 3


@dataclass(frozen=True)
class RelationshipPath:
    """A single traversal path from source to a reached target."""
    source: str                       # normalized query term
    relation_type: str
    target: str                       # normalized target value (last node in path)
    depth: int                        # number of hops (1 = direct)
    path: Tuple[str, ...]             # full node sequence, e.g. ("force", "acceleration", "velocity")
    provenance: Tuple[Provenance, ...]  # aggregated from all edges in this path


@dataclass(frozen=True)
class RelationshipClosureResult:
    source_term: str
    relation_type: str
    max_depth: int
    paths: Tuple[RelationshipPath, ...]
    fallback_used: bool


def compute_closure(
    term: str,
    relation_type: str,
    state: DiscourseState,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Tuple[RelationshipClosureResult, MultiHopTrace]:
    """
    BFS traversal from `term` over edges of `relation_type`.
    Returns (RelationshipClosureResult, MultiHopTrace).
    """
    norm_term = normalize_term(term)

    # Find source node by normalized value
    source_node = None
    for node in state.nodes.values():
        if normalize_term(str(node.value)) == norm_term:
            source_node = node
            break

    if source_node is None:
        result = RelationshipClosureResult(
            source_term=term,
            relation_type=relation_type,
            max_depth=max_depth,
            paths=(),
            fallback_used=True,
        )
        trace = MultiHopTrace(
            source_term=term,
            normalized_source=norm_term,
            relation_type=relation_type,
            max_depth=max_depth,
            visited_nodes=[],
            paths=[],
            cycle_detected=False,
            fallback_used=True,
        )
        return result, trace

    # BFS state: (node_id, path_tuple, path_node_ids, depth, accumulated_provenance)
    # path_node_ids tracks nodes IN THE CURRENT PATH to detect cycles without
    # blocking diamond-shaped graphs (same node reachable via distinct paths).
    queue: deque = deque()
    queue.append((source_node.id, (norm_term,), frozenset({source_node.id}), 0, ()))
    cycle_detected = False
    collected_paths: List[RelationshipPath] = []
    all_visited: Set[str] = {source_node.id}

    # Pre-index outgoing edges by source_id for efficiency
    edges_from: Dict[str, list] = {}
    for edge in state.edges:
        if edge.relation_type == relation_type:
            edges_from.setdefault(edge.source_id, []).append(edge)

    while queue:
        node_id, current_path, path_ids, depth, accumulated_prov = queue.popleft()

        for edge in edges_from.get(node_id, []):
            target_id = edge.target_id
            target_node = state.nodes.get(target_id)
            if target_node is None:
                continue

            target_val = normalize_term(str(target_node.value))
            new_path = current_path + (target_val,)
            new_depth = depth + 1
            new_prov = accumulated_prov + tuple(edge.provenance or ())

            if target_id in path_ids:
                # Cycle within this path — mark but don't emit or enqueue
                cycle_detected = True
                continue

            rel_path = RelationshipPath(
                source=norm_term,
                relation_type=relation_type,
                target=target_val,
                depth=new_depth,
                path=new_path,
                provenance=new_prov,
            )
            collected_paths.append(rel_path)
            all_visited.add(target_id)
            if new_depth < max_depth:
                queue.append((target_id, new_path, path_ids | {target_id}, new_depth, new_prov))

    # Sort: depth ASC, target ASC, path-string ASC
    collected_paths.sort(key=lambda p: (p.depth, p.target, " → ".join(p.path)))

    result = RelationshipClosureResult(
        source_term=term,
        relation_type=relation_type,
        max_depth=max_depth,
        paths=tuple(collected_paths),
        fallback_used=len(collected_paths) == 0,
    )
    trace = MultiHopTrace(
        source_term=term,
        normalized_source=norm_term,
        relation_type=relation_type,
        max_depth=max_depth,
        visited_nodes=list(all_visited),
        paths=[PathTrace(path=p.path, depth=p.depth, provenance_count=len(p.provenance))
               for p in collected_paths],
        cycle_detected=cycle_detected,
        fallback_used=result.fallback_used,
    )
    return result, trace
