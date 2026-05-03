"""
Paraphrase patterns for discourse.COMPOSE_RELATIONSHIPS.

Priority 196 for most; 202 for "ultimately based" (must beat definition at 200).

New paraphrases:
  "what indirectly affects X"
  "what is X ultimately based on"
  "derived dependencies of X"
  "indirect dependencies of X"
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

COMPOSITION_PARAPHRASE_PATTERNS = (
    PatternRule(
        id="para.cr.indirectly_affects",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("what", "indirectly", "affects"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="para.cr.ultimately_based_on",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("ultimately", "based"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        # Priority 202: "ultimately based" unambiguously signals composition
        # and must override the generic definition pattern (priority 200).
        priority=202,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="para.cr.derived_dependencies",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("derived", "dependencies"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="para.cr.indirect_dependencies",
        domain="discourse",
        operator_name="COMPOSE_RELATIONSHIPS",
        keywords=("indirect", "dependencies"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=196,
        arg_order=("term", "relation_type", "max_depth"),
    ),
)


def register_patterns(registry) -> None:
    for rule in COMPOSITION_PARAPHRASE_PATTERNS:
        registry.register(rule)
