"""
chunk_structured(doc_structure, source_path, source_title, ...) → Tuple[StructuredChunk, ...]

Splits each section's text into paragraph-sized chunks.
Chunks are rejected if shorter than min_chunk_chars.
chunk_id is a deterministic hash scoped to source_path + location + text.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from l_cdea.ingestion.document_scaling.section_model import (
    DocumentStructure,
    StructuredChunk,
)

MIN_CHUNK_CHARS = 40


def make_structured_chunk_id(source_path: str, location: str, text: str) -> str:
    """Deterministic chunk ID for structured chunks. Uses location instead of line_number."""
    content = f"{source_path}::document_structured::{location}::{text.strip().lower()}"
    return "chunk_" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def chunk_structured(
    doc_structure: DocumentStructure,
    source_path: str,
    source_title: str,
    min_chunk_chars: int = MIN_CHUNK_CHARS,
) -> Tuple[Tuple[StructuredChunk, ...], int]:
    """
    Return (accepted_chunks, rejected_count).
    Each accepted StructuredChunk carries section_id, heading, and location.
    """
    chunks = []
    rejected = 0

    for section in doc_structure.sections:
        if not section.text.strip():
            continue
        paragraphs = [p.strip() for p in section.text.split("\n\n") if p.strip()]
        for para_idx, para in enumerate(paragraphs):
            if len(para) < min_chunk_chars:
                rejected += 1
                continue
            location = f"section:{section.section_id}:para:{para_idx}"
            chunk_id = make_structured_chunk_id(source_path, location, para)
            chunks.append(StructuredChunk(
                chunk_id=chunk_id,
                section_id=section.section_id,
                heading=section.heading,
                text=para,
                paragraph_index=para_idx,
                location=location,
            ))

    return tuple(chunks), rejected
