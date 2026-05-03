from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class IntentFrame:
    """Resolved routing decision for a single query."""
    domain: str
    operator_name: str
    slots: Dict[str, str]
    confidence: float
    source_pattern_id: str
    fallback: bool
    # Mirrors PatternRule.arg_order; empty = V1 alphabetical fallback.
    arg_order: Tuple[str, ...] = ()

    @property
    def full_operator(self) -> str:
        return f"{self.domain}.{self.operator_name}"


@dataclass(frozen=True)
class PatternRule:
    """A registered domain pattern the router matches against."""
    id: str
    domain: str
    operator_name: str
    keywords: Tuple[str, ...]
    required_slots: Tuple[str, ...]
    optional_slots: Tuple[str, ...]
    priority: int = 100
    # V2: explicit slot → input_types positional mapping.
    # Empty tuple means V1 alphabetical fallback.
    arg_order: Tuple[str, ...] = ()

    @property
    def full_operator(self) -> str:
        return f"{self.domain}.{self.operator_name}"


@dataclass
class RouteResult:
    """Complete output of a routing decision."""
    intents: Tuple[IntentFrame, ...]
    selected_intent: IntentFrame
    ambiguous: bool
    fallback_used: bool


@dataclass
class RouteTrace:
    """Diagnostic trace of a routing decision."""
    input_text: str
    matched_patterns: List[str]
    rejected_patterns: List[str]
    slot_bindings: Dict[str, str]
    confidence_scores: Dict[str, float]
    selected_intent: IntentFrame
    ambiguous: bool
    fallback_used: bool


FALLBACK_INTENT = IntentFrame(
    domain="generic",
    operator_name="GENERIC_COMPILE",
    slots={},
    confidence=0.0,
    source_pattern_id="fallback.generic",
    fallback=True,
    arg_order=(),
)
