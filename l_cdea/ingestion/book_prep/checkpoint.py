"""
Checkpoint: records the last safely processed position in a book ingestion.
Stored as a dict inside BookManifest.last_checkpoint (not as a separate file).

Fields:
  book_id     — identifies the book
  chapter_id  — last completed chapter
  chunk_index — total chunks processed up to and including this chapter
  timestamp   — temporal_index at checkpoint time (monotonically increasing)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Checkpoint:
    book_id: str
    chapter_id: str
    chunk_index: int
    timestamp: int


def checkpoint_to_dict(cp: Checkpoint) -> dict:
    return {
        "book_id": cp.book_id,
        "chapter_id": cp.chapter_id,
        "chunk_index": cp.chunk_index,
        "timestamp": cp.timestamp,
    }


def checkpoint_from_dict(data: dict) -> Checkpoint:
    return Checkpoint(
        book_id=data["book_id"],
        chapter_id=data["chapter_id"],
        chunk_index=data["chunk_index"],
        timestamp=data["timestamp"],
    )
