"""
Metadata enrichment for structured document chunks.

build_metadata(chunk) → dict
  Returns node metadata dict including section context.

get_confidence_boost(chunk) → float
  Returns a confidence boost [0.0, 0.1] based on heading keywords.
  Boosts definitions found inside "Definitions", "Overview", or "Introduction" sections.
"""
from __future__ import annotations

from l_cdea.ingestion.document_scaling.section_model import StructuredChunk

_DEFINITION_SECTION_KEYWORDS = frozenset({"definition", "definitions", "overview", "introduction"})


def build_metadata(chunk: StructuredChunk, category: str = "content") -> dict:
    return {
        "category": category,
        "section_id": chunk.section_id,
        "heading": chunk.heading,
        "paragraph_index": chunk.paragraph_index,
        "location": chunk.location,
        "ingestion_mode": "document_structured",
    }


def get_confidence_boost(chunk: StructuredChunk) -> float:
    """Return confidence boost when the section heading signals definitions."""
    if chunk.heading is None:
        return 0.0
    lower = chunk.heading.lower()
    if any(kw in lower for kw in _DEFINITION_SECTION_KEYWORDS):
        return 0.1
    return 0.0


def heading_contains_term(chunk: StructuredChunk, term: str) -> bool:
    """True if the section heading contains the term (case-insensitive)."""
    if chunk.heading is None:
        return False
    return term.lower() in chunk.heading.lower()
