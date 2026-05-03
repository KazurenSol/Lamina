"""
l_cdea.core.router.paraphrase_patterns

Deterministic paraphrase pattern groups that expand the router's natural-language
coverage without changing operator semantics.

Groups:
  definition.py    — GET_DEFINITION paraphrases (priority 200)
  relationships.py — GET_RELATIONSHIPS one-hop (190) + GET_RELATIONSHIP_CLOSURE multi-hop (195)
  composition.py   — COMPOSE_RELATIONSHIPS (196 / 202 for "ultimately based")
  normalization.py — normalize_query() utility for pre-routing text cleanup
"""
from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query, normalize_tokens
from l_cdea.core.router.paraphrase_patterns.definition import DEFINITION_PARAPHRASE_PATTERNS
from l_cdea.core.router.paraphrase_patterns.relationships import (
    ONE_HOP_PARAPHRASE_PATTERNS,
    MULTI_HOP_PARAPHRASE_PATTERNS,
    ALL_RELATIONSHIP_PARAPHRASE_PATTERNS,
)
from l_cdea.core.router.paraphrase_patterns.composition import COMPOSITION_PARAPHRASE_PATTERNS


def register_patterns(registry) -> None:
    """Register all paraphrase patterns into the router registry."""
    from l_cdea.core.router.paraphrase_patterns import definition, relationships, composition
    definition.register_patterns(registry)
    relationships.register_patterns(registry)
    composition.register_patterns(registry)


__all__ = [
    "normalize_query",
    "normalize_tokens",
    "register_patterns",
    "DEFINITION_PARAPHRASE_PATTERNS",
    "ONE_HOP_PARAPHRASE_PATTERNS",
    "MULTI_HOP_PARAPHRASE_PATTERNS",
    "ALL_RELATIONSHIP_PARAPHRASE_PATTERNS",
    "COMPOSITION_PARAPHRASE_PATTERNS",
]
