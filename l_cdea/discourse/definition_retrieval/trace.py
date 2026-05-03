"""
DefinitionRetrievalTrace — observability record for a definition lookup.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DefinitionRetrievalTrace:
    term: str
    normalized_term: str
    matched_node_id: Optional[str]
    hit: bool
    returned_value: Optional[str]
    provenance_count: int
    fallback_used: bool
