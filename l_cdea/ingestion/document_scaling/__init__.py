"""
l_cdea.ingestion.document_scaling — structured document chunking.

Public API:
  parse_document(text)                    → DocumentStructure
  chunk_structured(doc_structure, ...)   → (Tuple[StructuredChunk, ...], int)
  build_metadata(chunk)                  → dict
  get_confidence_boost(chunk)            → float

Types:
  DocumentSection, StructuredChunk, DocumentStructure
  DocumentScalingTrace
"""
from l_cdea.ingestion.document_scaling.section_model import (
    DocumentSection,
    StructuredChunk,
    DocumentStructure,
)
from l_cdea.ingestion.document_scaling.parser import parse_document
from l_cdea.ingestion.document_scaling.chunker import chunk_structured, make_structured_chunk_id
from l_cdea.ingestion.document_scaling.metadata import (
    build_metadata,
    get_confidence_boost,
    heading_contains_term,
)
from l_cdea.ingestion.document_scaling.trace import DocumentScalingTrace

__all__ = [
    "parse_document",
    "chunk_structured",
    "make_structured_chunk_id",
    "build_metadata",
    "get_confidence_boost",
    "heading_contains_term",
    "DocumentSection",
    "StructuredChunk",
    "DocumentStructure",
    "DocumentScalingTrace",
]
