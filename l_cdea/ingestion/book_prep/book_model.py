"""Core types for book ingestion."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class BookMetadata:
    book_id: str
    title: Optional[str]
    author: Optional[str]
    source_path: str
    total_lines: int


@dataclass(frozen=True)
class BookChapter:
    chapter_id: str
    title: Optional[str]
    start_line: int
    end_line: int
    section_ids: Tuple[str, ...]


@dataclass(frozen=True)
class BookStructure:
    metadata: BookMetadata
    chapters: Tuple[BookChapter, ...]
