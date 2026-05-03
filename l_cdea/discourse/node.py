from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Tuple

from l_cdea.core.types.base import SemanticType

BASE_SALIENCE: float = 1.0
REINFORCEMENT: float = 0.5


@dataclass
class DiscourseNode:
    id: str
    semantic_type: SemanticType
    value: Any
    salience: float
    created_at: int    # temporal index at creation
    updated_at: int    # temporal index at last update
    provenance: tuple = field(default_factory=tuple)  # Tuple[Provenance, ...]
    metadata: dict = field(default_factory=dict)      # domain-specific tags (e.g. category, term)


def make_node_id(semantic_type: SemanticType, value: Any) -> str:
    """Deterministic node ID from type + value. Same content always produces same ID."""
    content = f"{semantic_type.value}::{repr(value)}"
    return "dn_" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
