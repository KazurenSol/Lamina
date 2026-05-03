"""
l_cdea.ingestion.modes — ingestion mode configuration and filtering.

Public API:
  validate_mode(mode)             → None or raises ValueError
  get_mode_config(mode)           → IngestionModeConfig
  is_valid_dictionary_chunk(text) → bool
  IngestionModeConfig
  IngestionModeTrace
"""
from __future__ import annotations

from dataclasses import dataclass

from l_cdea.ingestion.modes.config import (
    VALID_MODES,
    IngestionModeConfig,
    DOCUMENT_MODE,
    DICTIONARY_MODE,
    DOCUMENT_STRUCTURED_MODE,
    get_mode_config,
    validate_mode,
)
from l_cdea.ingestion.modes.filter import is_valid_dictionary_chunk


@dataclass
class IngestionModeTrace:
    mode: str
    min_chunk_chars: int
    accepted_chunks: int
    rejected_chunks: int


__all__ = [
    "VALID_MODES",
    "IngestionModeConfig",
    "DOCUMENT_MODE",
    "DICTIONARY_MODE",
    "DOCUMENT_STRUCTURED_MODE",
    "get_mode_config",
    "validate_mode",
    "is_valid_dictionary_chunk",
    "IngestionModeTrace",
]
