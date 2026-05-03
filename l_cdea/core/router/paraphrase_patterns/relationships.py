"""
Paraphrase patterns for relationship queries.

One-hop (GET_RELATIONSHIPS, priority 190):
  "what affects X"
  "what influences X"
  "what is X based on"   → uses priority 201 to beat definition (200) when "based on" present
  "what determines X"
  "dependencies of X"
  "what does X rely on"

Multi-hop closure (GET_RELATIONSHIP_CLOSURE, priority 195):
  "full dependencies of X"
  "all dependencies of X"
  "dependency graph for X"
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

ONE_HOP_PARAPHRASE_PATTERNS = (
    PatternRule(
        id="para.rel.what_affects",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "affects"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="para.rel.what_influences",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "influences"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="para.rel.based_on",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("based", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        # Priority 201 beats definition (200) when "based on" is present —
        # presence of "based on" unambiguously signals a relationship query.
        priority=201,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="para.rel.what_determines",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "determines"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="para.rel.dependencies_of",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
    PatternRule(
        id="para.rel.rely_on",
        domain="discourse",
        operator_name="GET_RELATIONSHIPS",
        keywords=("what", "does", "rely", "on"),
        required_slots=("term", "relation_type"),
        optional_slots=(),
        priority=190,
        arg_order=("term", "relation_type"),
    ),
)

MULTI_HOP_PARAPHRASE_PATTERNS = (
    PatternRule(
        id="para.mh.full_dependencies",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("full", "dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="para.mh.all_dependencies",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("all", "dependencies", "of"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
    PatternRule(
        id="para.mh.dependency_graph",
        domain="discourse",
        operator_name="GET_RELATIONSHIP_CLOSURE",
        keywords=("dependency", "graph", "for"),
        required_slots=("term", "relation_type"),
        optional_slots=("max_depth",),
        priority=195,
        arg_order=("term", "relation_type", "max_depth"),
    ),
)

ALL_RELATIONSHIP_PARAPHRASE_PATTERNS = ONE_HOP_PARAPHRASE_PATTERNS + MULTI_HOP_PARAPHRASE_PATTERNS


def register_patterns(registry) -> None:
    for rule in ALL_RELATIONSHIP_PARAPHRASE_PATTERNS:
        registry.register(rule)
