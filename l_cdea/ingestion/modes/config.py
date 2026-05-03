"""
Ingestion mode configuration.

Modes:
  "document"            — textbooks, articles, long-form content (MIN_CHUNK_CHARS=40)
  "dictionary"          — glossaries, definition lists, short structured entries (MIN_CHUNK_CHARS=5)
  "document_structured" — heading-aware structured chunking with section context
  "book"                — multi-chapter books with manifest, checkpoint, and resume support
"""
from __future__ import annotations

from dataclasses import dataclass

VALID_MODES = frozenset({"document", "dictionary", "document_structured", "book"})


@dataclass(frozen=True)
class IngestionModeConfig:
    mode: str
    min_chunk_chars: int
    definition_priority_boost: int  # added to definition category score in classifier
    confidence_weight_override: float | None  # replaces 0.70 weight for definition+document


DOCUMENT_MODE = IngestionModeConfig(
    mode="document",
    min_chunk_chars=40,
    definition_priority_boost=0,
    confidence_weight_override=None,
)

DICTIONARY_MODE = IngestionModeConfig(
    mode="dictionary",
    min_chunk_chars=5,
    definition_priority_boost=4,   # lifts definition over claim/example in scoring
    confidence_weight_override=0.85,  # higher confidence weight for validated definitions
)

DOCUMENT_STRUCTURED_MODE = IngestionModeConfig(
    mode="document_structured",
    min_chunk_chars=40,
    definition_priority_boost=0,
    confidence_weight_override=None,
)

BOOK_MODE = IngestionModeConfig(
    mode="book",
    min_chunk_chars=40,
    definition_priority_boost=0,
    confidence_weight_override=None,
)

_MODE_MAP = {
    "document":             DOCUMENT_MODE,
    "dictionary":           DICTIONARY_MODE,
    "document_structured":  DOCUMENT_STRUCTURED_MODE,
    "book":                 BOOK_MODE,
}


def get_mode_config(mode: str) -> IngestionModeConfig:
    return _MODE_MAP[mode]


def validate_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        raise ValueError(
            f"Invalid ingestion mode {mode!r}. Valid modes: {sorted(VALID_MODES)}"
        )
