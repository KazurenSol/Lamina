"""Observability types returned by ingest_book()."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class GlossaryModeTrace:
    chapter_id: str
    glossary_mode: bool
    total_lines: int
    valid_lines: int
    ratio: float


@dataclass(frozen=True)
class BookIngestionTrace:
    book_id: str
    chapters_total: int
    chapters_processed: int
    chunks_processed: int
    nodes_added: int
    edges_added: int
    resumed: bool
    chapter_modes: Tuple[GlossaryModeTrace, ...] = ()
