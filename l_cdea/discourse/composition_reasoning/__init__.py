"""
l_cdea.discourse.composition_reasoning — deterministic relationship composition.

Public API:
  compose(term, relation_type, state, max_depth) → (CompositionResult, CompositionTrace)

Types:
  ComposedRelationship
  CompositionResult
  CompositionTrace
  ComposedItem
"""
from l_cdea.discourse.composition_reasoning.rules import (
    ComposedRelationship,
    CompositionResult,
    apply_rules,
)
from l_cdea.discourse.composition_reasoning.composer import compose, DEFAULT_MAX_DEPTH
from l_cdea.discourse.composition_reasoning.trace import CompositionTrace, ComposedItem

__all__ = [
    "compose",
    "apply_rules",
    "ComposedRelationship",
    "CompositionResult",
    "CompositionTrace",
    "ComposedItem",
    "DEFAULT_MAX_DEPTH",
]
