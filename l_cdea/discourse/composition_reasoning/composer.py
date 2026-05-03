"""
compose(term, relation_type, state, max_depth) → (CompositionResult, CompositionTrace)

Calls multi-hop traversal then applies composition rules.
Never mutates DiscourseState.
"""
from __future__ import annotations

from typing import Tuple

from l_cdea.discourse.state import DiscourseState
from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
from l_cdea.discourse.composition_reasoning.rules import (
    apply_rules, ComposedRelationship, CompositionResult,
)
from l_cdea.discourse.composition_reasoning.trace import CompositionTrace, ComposedItem

DEFAULT_MAX_DEPTH = 3


def compose(
    term: str,
    relation_type: str,
    state: DiscourseState,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Tuple[CompositionResult, CompositionTrace]:
    """Run BFS traversal and apply composition rules. Read-only — state is never modified."""
    closure_result, _ = compute_closure(term, relation_type, state, max_depth)

    if closure_result.fallback_used or not closure_result.paths:
        result = CompositionResult(
            source_term=term,
            relation_type=relation_type,
            direct=(),
            indirect=(),
            fallback_used=True,
        )
        trace = CompositionTrace(
            source_term=term,
            relation_type=relation_type,
            max_depth=max_depth,
            input_paths=0,
            composed_direct=[],
            composed_indirect=[],
            fallback_used=True,
        )
        return result, trace

    result = apply_rules(closure_result)

    trace = CompositionTrace(
        source_term=term,
        relation_type=relation_type,
        max_depth=max_depth,
        input_paths=len(closure_result.paths),
        composed_direct=[
            ComposedItem(target=cr.target, paths=cr.paths, provenance_count=len(cr.provenance))
            for cr in result.direct
        ],
        composed_indirect=[
            ComposedItem(target=cr.target, paths=cr.paths, provenance_count=len(cr.provenance))
            for cr in result.indirect
        ],
        fallback_used=result.fallback_used,
    )
    return result, trace
