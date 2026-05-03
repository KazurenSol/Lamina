"""
l_cdea.discourse.relationship_query — query stored relationship edges.

Public API:
  lookup_relationships(term, relation_type, state) → (RelationshipLookupResult, RelationshipQueryTrace)
  normalize_term(term)                             → str
  normalize_relation_type(text)                    → str

Types:
  RelationshipLookupResult
  RelationshipQueryTrace
"""
from l_cdea.discourse.relationship_query.normalization import normalize_term, normalize_relation_type
from l_cdea.discourse.relationship_query.lookup import (
    RelationshipLookupResult,
    lookup_relationships,
)
from l_cdea.discourse.relationship_query.trace import RelationshipQueryTrace

__all__ = [
    "normalize_term",
    "normalize_relation_type",
    "RelationshipLookupResult",
    "RelationshipQueryTrace",
    "lookup_relationships",
]
