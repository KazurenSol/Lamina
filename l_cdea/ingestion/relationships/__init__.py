"""
l_cdea.ingestion.relationships — deterministic relationship extraction.

Public API:
  extract_relationships(chunk_text, provenance) → RelationshipExtractionResult
  build_edges(edges, discourse_state)           → int  (edges added)
  normalize_term(term)                          → str

Types:
  RelationshipEdge
  RelationshipExtractionResult
  RelationshipTrace
"""
from l_cdea.ingestion.relationships.normalizer import normalize_term
from l_cdea.ingestion.relationships.extractor import (
    RelationshipEdge,
    RelationshipExtractionResult,
    extract_relationships,
)
from l_cdea.ingestion.relationships.edge_builder import build_edges
from l_cdea.ingestion.relationships.trace import RelationshipTrace

__all__ = [
    "normalize_term",
    "RelationshipEdge",
    "RelationshipExtractionResult",
    "RelationshipTrace",
    "extract_relationships",
    "build_edges",
]
