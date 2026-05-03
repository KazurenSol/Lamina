"""
Router patterns for discourse.GET_RELATIONSHIP_CLOSURE.

Priority 195 — above one-hop GET_RELATIONSHIPS (190) and below GET_DEFINITION (200).
This ensures "what does X ultimately depend on" reaches multi-hop, not one-hop.

V1 supported patterns (all default to depends_on / max_depth=3):
  "what does X ultimately depend on"
  "what does X indirectly depend on"
  "what are all dependencies of X"
  "show dependency chain for X"
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

MULTI_HOP_PATTERNS = (
    PatternRule(
        id="discourse.mh.ultimately_depends_on",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("what", "does", "ultimately", "depend", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.mh.indirectly_depends_on",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("what", "does", "indirectly", "depend", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.mh.all_dependencies",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("what", "are", "all", "dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.mh.dependency_chain",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("show", "dependency", "chain", "for"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
)


def register_patterns(registry) -> None:
    for rule in MULTI_HOP_PATTERNS:
        registry.register(rule)
