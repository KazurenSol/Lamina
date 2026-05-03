"""
Router patterns for discourse.GET_DEFINITION.

Priority 200 (vs domain default 100) ensures definition-query patterns
suppress action operators when the query is definitional in form.

Patterns:
  "what is X"           keywords=(what, is)
  "what is a X"         keywords=(what, is, a)    — "a" filtered at slot-fill
  "what is an X"        keywords=(what, is, an)   — "an" filtered at slot-fill
  "define X"            keywords=(define,)
  "definition of X"     keywords=(definition, of)
  "what does X mean"    keywords=(what, does, mean)
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

DEFINITION_PATTERNS = (
    PatternRule(
        id="discourse.def.what_is",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("what", "is"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="discourse.def.define",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("define",),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="discourse.def.definition_of",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("definition", "of"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="discourse.def.what_does_mean",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("what", "does", "mean"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
)


def register_patterns(registry) -> None:
    """Register all definition patterns into the router PatternRegistry."""
    for rule in DEFINITION_PATTERNS:
        registry.register(rule)
