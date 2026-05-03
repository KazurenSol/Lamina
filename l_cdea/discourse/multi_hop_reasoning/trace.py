"""
Observability types for multi-hop relationship reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PathTrace:
    path: Tuple[str, ...]
    depth: int
    provenance_count: int


@dataclass
class MultiHopTrace:
    source_term: str
    normalized_source: str
    relation_type: str
    max_depth: int
    visited_nodes: List[str]
    paths: List[PathTrace]
    cycle_detected: bool
    fallback_used: bool
