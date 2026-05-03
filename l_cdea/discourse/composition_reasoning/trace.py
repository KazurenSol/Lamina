"""
Observability types for composition reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class ComposedItem:
    target: str
    paths: Tuple[Tuple[str, ...], ...]
    provenance_count: int


@dataclass
class CompositionTrace:
    source_term: str
    relation_type: str
    max_depth: int
    input_paths: int
    composed_direct: List[ComposedItem]
    composed_indirect: List[ComposedItem]
    fallback_used: bool
