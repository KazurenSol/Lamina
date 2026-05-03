"""
Extract step-by-step procedures from document chunks.
V1: numbered or bulleted lists, or sentences containing "first", "then", "finally".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from l_cdea.ingestion.chunker import DocumentChunk

_STEP_PATTERN = re.compile(r"^\s*(?:\d+[.)]\s+|[-•]\s+)(.+)", re.MULTILINE)
_SEQUENCE_WORDS = re.compile(r"\b(first|second|third|then|next|finally|lastly)\b", re.IGNORECASE)


@dataclass
class ExtractedProcedure:
    name: str
    steps: List[str]
    source_title: str
    source_path: str
    paragraph_index: int
    confidence: float = 0.75
    extraction_method: str = "list_v1"


def extract_procedures(chunk: DocumentChunk) -> List[ExtractedProcedure]:
    # Try numbered/bulleted list extraction
    matches = _STEP_PATTERN.findall(chunk.text)
    if len(matches) >= 2:
        return [ExtractedProcedure(
            name=f"procedure_p{chunk.paragraph_index}",
            steps=[m.strip() for m in matches],
            source_title=chunk.source_title,
            source_path=chunk.source_path,
            paragraph_index=chunk.paragraph_index,
        )]

    # Try sequence-word extraction
    sentences = [s.strip() for s in chunk.text.split(".") if _SEQUENCE_WORDS.search(s)]
    if len(sentences) >= 2:
        return [ExtractedProcedure(
            name=f"sequence_p{chunk.paragraph_index}",
            steps=sentences,
            source_title=chunk.source_title,
            source_path=chunk.source_path,
            paragraph_index=chunk.paragraph_index,
            confidence=0.6,
            extraction_method="sequence_v1",
        )]

    return []
