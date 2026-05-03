"""
Extract definitions from document chunks.
V1: sentences matching "X is ...", "X means ...", "X refers to ..." patterns.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from l_cdea.ingestion.chunker import DocumentChunk


_DEFINITION_PATTERNS = [
    re.compile(r"^([A-Z][^.]{1,60}) is ([^.]+)\.", re.IGNORECASE),
    re.compile(r"^([A-Z][^.]{1,60}) means ([^.]+)\.", re.IGNORECASE),
    re.compile(r"^([A-Z][^.]{1,60}) refers to ([^.]+)\.", re.IGNORECASE),
    re.compile(r"^([A-Z][^.]{1,60}) (?:is defined as|is known as) ([^.]+)\.", re.IGNORECASE),
]


_DEFINITION_HEADING_KEYWORDS = frozenset({"definition", "definitions", "overview", "introduction"})


@dataclass
class ExtractedDefinition:
    term: str
    definition: str
    source_title: str
    source_path: str
    paragraph_index: int
    confidence: float = 0.8
    extraction_method: str = "pattern_v1"
    chunk_id: Optional[str] = None   # stable hash from source chunk (dictionary / structured modes)
    location: Optional[str] = None   # e.g. "line:3" or "section:<id>:para:<n>"
    section_id: Optional[str] = None # structured mode only
    heading: Optional[str] = None    # structured mode only


def _heading_confidence_boost(heading: Optional[str]) -> float:
    """Return +0.1 if the section heading suggests a definitions context."""
    if heading is None:
        return 0.0
    if any(kw in heading.lower() for kw in _DEFINITION_HEADING_KEYWORDS):
        return 0.1
    return 0.0


def extract_definitions(chunk: DocumentChunk) -> List[ExtractedDefinition]:
    base_confidence = 0.8 + _heading_confidence_boost(chunk.heading)
    sentences = [s.strip() + "." for s in chunk.text.split(".") if len(s.strip()) > 15]
    definitions = []
    for sent in sentences:
        for pat in _DEFINITION_PATTERNS:
            m = pat.match(sent)
            if m:
                definitions.append(ExtractedDefinition(
                    term=m.group(1).strip(),
                    definition=m.group(2).strip(),
                    source_title=chunk.source_title,
                    source_path=chunk.source_path,
                    paragraph_index=chunk.paragraph_index,
                    confidence=base_confidence,
                    chunk_id=chunk.chunk_id,
                    location=chunk.location,
                    section_id=chunk.section_id,
                    heading=chunk.heading,
                ))
                break
    return definitions
