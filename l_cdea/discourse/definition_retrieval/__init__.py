"""
l_cdea.discourse.definition_retrieval — definition query resolution.

Public API:
  register_definition(term, text, source_id, confidence, ...)
  lookup_definition(term, state=None) → DefinitionLookupResult
  clear_definitions()

Types:
  DefinitionEntry
  DefinitionLookupResult
  DefinitionRetrievalTrace
"""
from l_cdea.discourse.definition_retrieval.normalization import normalize_term
from l_cdea.discourse.definition_retrieval.lookup import (
    DefinitionEntry,
    DefinitionLookupResult,
    register_definition,
    lookup_definition,
    clear_definitions,
)
from l_cdea.discourse.definition_retrieval.trace import DefinitionRetrievalTrace
from l_cdea.discourse.definition_retrieval.operator import (
    GET_DEFINITION,
    register_discourse_operators,
    register_governed_operators,
)
from l_cdea.discourse.definition_retrieval.patterns import DEFINITION_PATTERNS, register_patterns

__all__ = [
    "normalize_term",
    "DefinitionEntry",
    "DefinitionLookupResult",
    "DefinitionRetrievalTrace",
    "register_definition",
    "lookup_definition",
    "clear_definitions",
    "GET_DEFINITION",
    "register_discourse_operators",
    "register_governed_operators",
    "DEFINITION_PATTERNS",
    "register_patterns",
]
