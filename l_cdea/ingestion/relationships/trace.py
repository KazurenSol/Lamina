"""
Observability types for relationship extraction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class RelationshipTrace:
    chunk_text: str
    matched_pattern: Optional[str]        # pattern name, or None if no match
    extracted_edges: List[Tuple[str, str, str]]  # (source, relation, target) — raw strings
    normalized_terms: List[Tuple[str, str]]      # [(raw_term, normalized_term), ...]
