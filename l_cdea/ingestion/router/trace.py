"""
IngestionRouteTrace — observability record for a single routing decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class IngestionRouteTrace:
    chunk_text: str
    matched_patterns: Tuple[str, ...]
    selected_category: str
    confidence: float
    ambiguous: bool
    fallback: bool
