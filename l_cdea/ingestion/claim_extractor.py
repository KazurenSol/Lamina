"""
Extract factual claims from document chunks.
V1: heuristic extraction — sentences ending with '.' that are not questions/definitions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from l_cdea.ingestion.chunker import DocumentChunk


@dataclass
class ExtractedClaim:
    text: str
    source_title: str
    source_path: str
    paragraph_index: int
    confidence: float = 0.7
    extraction_method: str = "heuristic_v1"


def extract_claims(chunk: DocumentChunk) -> List[ExtractedClaim]:
    sentences = [s.strip() for s in chunk.text.split(".") if s.strip()]
    claims = []
    for sent in sentences:
        if sent.endswith("?") or sent.lower().startswith("define") or sent.lower().startswith("step"):
            continue
        if len(sent) < 20:
            continue
        claims.append(ExtractedClaim(
            text=sent + ".",
            source_title=chunk.source_title,
            source_path=chunk.source_path,
            paragraph_index=chunk.paragraph_index,
        ))
    return claims
