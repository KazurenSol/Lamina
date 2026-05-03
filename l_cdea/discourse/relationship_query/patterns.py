"""
Router patterns for discourse.GET_RELATIONSHIPS.

Priority 190 — above domain operators (100) but below GET_DEFINITION (200).
This ensures "what does X depend on" routes to relationship query, not generic,
while "what is X" still routes to GET_DEFINITION.

V1 supported patterns:
  "what does X depend on"   → depends_on
  "what is X related to"    → related_to
  "what causes X"           → causes  (inverse)
  "what is part of X"       → part_of (inverse)
  "what is X part of"       → part_of (forward)
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

RELATIONSHIP_PATTERNS = (
    PatternRule(
        id="discourse.rel.depends_on",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "does", "depend", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="discourse.rel.related_to",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "is", "related", "to"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="discourse.rel.causes",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "causes"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="discourse.rel.part_of_fwd",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "is", "part", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
)


def register_patterns(registry) -> None:
    """Register all relationship-query patterns into the router PatternRegistry."""
    for rule in RELATIONSHIP_PATTERNS:
        registry.register(rule)
