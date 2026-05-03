"""
Semantic chunker: sentence-first, coherence-grouped.

Works for all structured text types: dictionaries, book passages, articles.
(Conversational utterances — single words, dialogue turns — belong in the
experience layer, not here.)

Public API:
  chunk_semantic(doc: RawDocument) -> Tuple[List[DocumentChunk], int]
"""
from __future__ import annotations

from typing import List, Tuple

from l_cdea.ingestion.chunker import DocumentChunk
from l_cdea.ingestion.chunk_ids import make_chunk_id
from l_cdea.ingestion.document_loader import RawDocument
from l_cdea.ingestion.semantic_chunker.sentence_splitter import split_sentences
from l_cdea.ingestion.semantic_chunker.coherence_grouper import group_sentences

MIN_CHUNK_CHARS = 10


def chunk_semantic(doc: RawDocument) -> Tuple[List[DocumentChunk], int]:
    sentences = split_sentences(doc.content)
    if not sentences:
        return [], 0

    groups = group_sentences(sentences)
    accepted: List[DocumentChunk] = []
    rejected = 0

    for group_idx, group in enumerate(groups):
        text = group.text()
        if len(text) < MIN_CHUNK_CHARS:
            rejected += 1
            continue

        chunk_id = make_chunk_id(doc.source_path, "semantic", group_idx, text)
        accepted.append(DocumentChunk(
            text=text,
            source_title=doc.title,
            source_path=doc.source_path,
            paragraph_index=group.paragraph_index,
            author=doc.author,
            chunk_id=chunk_id,
            location=f"semantic:para:{group.paragraph_index}:group:{group_idx}",
        ))

    return accepted, rejected


__all__ = ["chunk_semantic"]
