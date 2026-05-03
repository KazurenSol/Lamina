"""
Split a RawDocument into paragraph-sized chunks with position metadata.

Two modes:
  "document"   — split on double-newlines, MIN_CHUNK_CHARS=40
  "dictionary" — split on single lines, MIN_CHUNK_CHARS=5,
                 with verb/completeness filter; each line is one chunk
                 with a stable chunk_id and line-level location.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from l_cdea.ingestion.document_loader import RawDocument

MIN_CHUNK_CHARS = 40  # document mode default; dictionary mode uses 5


@dataclass
class DocumentChunk:
    text: str
    source_title: str
    source_path: str
    paragraph_index: int
    author: Optional[str] = None
    chunk_id: Optional[str] = None    # stable hash; set in dictionary / structured modes
    location: Optional[str] = None    # e.g. "line:3" or "section:<id>:para:<n>"
    section_id: Optional[str] = None  # structured mode only
    heading: Optional[str] = None     # structured mode only


def chunk_document(
    doc: RawDocument,
    min_chars: int = MIN_CHUNK_CHARS,
    mode: str = "document",
) -> List[DocumentChunk]:
    chunks, _ = chunk_document_with_trace(doc, mode=mode)
    return chunks


def chunk_document_with_trace(
    doc: RawDocument,
    mode: str = "document",
) -> Tuple[List[DocumentChunk], int]:
    """
    Return (accepted_chunks, rejected_count).

    document mode  — paragraph-based (split on blank lines), MIN_CHUNK_CHARS=40.
    dictionary mode — line-based (each line is one chunk), MIN_CHUNK_CHARS=5,
                      with verb-presence filter and stable chunk_id per line.
    """
    from l_cdea.ingestion.modes.config import get_mode_config

    cfg = get_mode_config(mode)
    effective_min = cfg.min_chunk_chars

    if mode == "dictionary":
        return _chunk_dictionary(doc, effective_min)
    else:
        return _chunk_document(doc, effective_min)


# ── Document mode ─────────────────────────────────────────────────────────────

def _chunk_document(doc: RawDocument, min_chars: int) -> Tuple[List[DocumentChunk], int]:
    paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
    chunks: List[DocumentChunk] = []
    rejected = 0
    for i, para in enumerate(paragraphs):
        if len(para) < min_chars:
            rejected += 1
            continue
        chunks.append(DocumentChunk(
            text=para,
            source_title=doc.title,
            source_path=doc.source_path,
            paragraph_index=i,
            author=doc.author,
        ))
    return chunks, rejected


# ── Dictionary mode ───────────────────────────────────────────────────────────

def _chunk_dictionary(doc: RawDocument, min_chars: int) -> Tuple[List[DocumentChunk], int]:
    from l_cdea.ingestion.modes.filter import is_valid_dictionary_chunk
    from l_cdea.ingestion.chunk_ids import make_chunk_id

    chunks: List[DocumentChunk] = []
    rejected = 0

    for line_num, raw_line in enumerate(doc.content.split("\n"), start=1):
        line = raw_line.strip()
        if not line:
            continue  # blank lines silently skipped (not counted as rejected)
        if len(line) < min_chars or not is_valid_dictionary_chunk(line):
            rejected += 1
            continue
        chunk_id = make_chunk_id(doc.source_path, "dictionary", line_num, line)
        chunks.append(DocumentChunk(
            text=line,
            source_title=doc.title,
            source_path=doc.source_path,
            paragraph_index=line_num,
            author=doc.author,
            chunk_id=chunk_id,
            location=f"line:{line_num}",
        ))

    return chunks, rejected
