"""
l_cdea.discourse.multi_hop_reasoning — deterministic BFS graph reasoning.

Public API:
  compute_closure(term, relation_type, state, max_depth) → (RelationshipClosureResult, MultiHopTrace)

Types:
  RelationshipPath
  RelationshipClosureResult
  MultiHopTrace
  PathTrace
"""
from l_cdea.discourse.multi_hop_reasoning.traversal import (
    RelationshipPath,
    RelationshipClosureResult,
    compute_closure,
    DEFAULT_MAX_DEPTH,
)
from l_cdea.discourse.multi_hop_reasoning.trace import MultiHopTrace, PathTrace

__all__ = [
    "RelationshipPath",
    "RelationshipClosureResult",
    "MultiHopTrace",
    "PathTrace",
    "compute_closure",
    "DEFAULT_MAX_DEPTH",
]
