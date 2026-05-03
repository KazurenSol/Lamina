"""
ValidationTrace — full observability record for a single validation decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ValidationTrace:
    input_value: Any
    duplicate_of: Optional[str]   # node_id of the duplicate, or None
    conflict_with: Optional[str]  # node_id of the conflicting node, or None
    score: float
    decision: str                 # "accept" | "reject" | "merge" | "conflict"
    reason: str
