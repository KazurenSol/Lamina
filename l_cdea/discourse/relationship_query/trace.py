"""
Observability type for relationship query execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RelationshipQueryTrace:
    term: str
    normalized_term: str
    relation_type: str
    matched_source_node_id: Optional[str]
    matched_edges: List[Dict]            # per-edge dicts: target_value, provenance_entries, …
    returned_values: List[str]
    hit: bool
    fallback_used: bool
