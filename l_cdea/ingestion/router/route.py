"""
Core routing types for the ingestion router.

IngestionRoute — a single chunk's classification and routing decision.
IngestionRouteResult — the result of routing a batch of chunks.

Categories:
  "definition"  — describes what something is
  "claim"       — states a fact or relationship
  "procedure"   — describes a process or steps
  "example"     — demonstrates usage or instance
  "formula"     — mathematical or symbolic expression
  "unknown"     — fallback category
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Tuple

CATEGORIES = frozenset({
    "definition", "claim", "procedure", "example", "formula", "unknown",
})


@dataclass(frozen=True)
class IngestionRoute:
    """Classification and routing decision for a single text chunk."""
    route_id: str                     # deterministic: sha256(chunk_text)[:12]
    chunk_text: str
    category: str                     # one of CATEGORIES
    confidence: float                 # 0.0–1.0
    matched_patterns: Tuple[str, ...] # IDs of PatternRules that matched
    fallback: bool                    # True only when category == "unknown"

    def __post_init__(self):
        if self.category not in CATEGORIES:
            raise ValueError(f"Invalid category: {self.category!r}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


@dataclass(frozen=True)
class IngestionRouteResult:
    """Result of routing one or more chunks."""
    routes: Tuple[IngestionRoute, ...]
    ambiguous: bool   # True if any route had tied scores


def make_route_id(chunk_text: str, index: int = 0) -> str:
    """Deterministic route ID: sha256(chunk_text)[:10] + positional suffix."""
    digest = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:10]
    return f"{digest}:{index}"
