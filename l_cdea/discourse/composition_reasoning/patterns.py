"""
Router patterns for discourse.COMPOSE_RELATIONSHIPS.

Priority 196 — above multi-hop GET_RELATIONSHIP_CLOSURE (195).
Composition gives direct/indirect separation; multi-hop gives flat paths.

V1 patterns:
  "what does X indirectly depend on"
  "what does X ultimately depend on"   (aliases multi-hop at higher priority)
  "what are indirect dependencies of X"
  "derive dependencies of X"
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

COMPOSITION_PATTERNS = (
    PatternRule(
        id="discourse.cr.indirectly_depends_on",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("what", "does", "indirectly", "depend", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.cr.ultimately_depends_on",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("what", "does", "ultimately", "depend", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.cr.indirect_dependencies",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("what", "are", "indirect", "dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="discourse.cr.derive_dependencies",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("derive", "dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
)


def register_patterns(registry) -> None:
    for rule in COMPOSITION_PATTERNS:
        registry.register(rule)
