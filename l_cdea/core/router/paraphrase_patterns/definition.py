"""
Paraphrase patterns for discourse.GET_DEFINITION.

Priority 200 — same group as canonical definition patterns.

New paraphrases:
  "explain X"
  "tell me about X"
  "what is X about"
  "give definition of X"
"""
from __future__ import annotations

from l_cdea.core.router.intent import PatternRule

DEFINITION_PARAPHRASE_PATTERNS = (
    PatternRule(
        id="para.def.explain",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("explain",),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="para.def.tell_me_about",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("tell", "about"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="para.def.what_is_about",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("what", "is", "about"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
    PatternRule(
        id="para.def.give_definition",
        domain="discourse",
        operator_name="GET_DEFINITION",
        keywords=("give", "definition"),
        required_slots=("term",),
        optional_slots=(),
        priority=200,
        arg_order=("term",),
    ),
)


def register_patterns(registry) -> None:
    for rule in DEFINITION_PARAPHRASE_PATTERNS:
        registry.register(rule)
