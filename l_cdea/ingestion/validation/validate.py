"""
validate(value, state) → ValidationDecision
validate_with_trace(value, state) → (ValidationDecision, ValidationTrace)

Validation flow (hard rule: NO DiscourseState mutation here):
  1. detect_duplicate  — exact / canonical / dataset match
  2. detect_conflict   — same extraction context, different value
  3. compute_score     — provenance quality signal
  4. apply_rules       — deterministic decision from the above
"""
from __future__ import annotations

from typing import Tuple

from l_cdea.discourse.provenance.model import ProvenancedValue
from l_cdea.discourse.state import DiscourseState
from l_cdea.ingestion.validation.duplicate import detect_duplicate
from l_cdea.ingestion.validation.conflict import detect_conflict
from l_cdea.ingestion.validation.scoring import compute_score
from l_cdea.ingestion.validation.rules import (
    ValidationDecision,
    ValidatedKnowledge,
    apply_rules,
)
from l_cdea.ingestion.validation.trace import ValidationTrace


def validate(
    value: ProvenancedValue,
    state: DiscourseState,
) -> ValidationDecision:
    """Classify a ProvenancedValue without mutating DiscourseState."""
    duplicate_of = detect_duplicate(value, state)
    conflict_with = detect_conflict(value, state)
    score = compute_score(value)
    return apply_rules(value, duplicate_of, conflict_with, score)


def validate_with_trace(
    value: ProvenancedValue,
    state: DiscourseState,
) -> Tuple[ValidationDecision, ValidationTrace]:
    """Classify with full trace for observability."""
    duplicate_of = detect_duplicate(value, state)
    conflict_with = detect_conflict(value, state)
    score = compute_score(value)
    decision = apply_rules(value, duplicate_of, conflict_with, score)
    trace = ValidationTrace(
        input_value=value.value,
        duplicate_of=duplicate_of,
        conflict_with=conflict_with,
        score=score,
        decision=decision.status,
        reason=decision.reason,
    )
    return decision, trace


def validate_batch(
    values: tuple,
    state: DiscourseState,
) -> Tuple[ValidatedKnowledge, ...]:
    """Validate a sequence of ProvenancedValues against the same state snapshot."""
    return tuple(
        ValidatedKnowledge(value=v, decision=validate(v, state))
        for v in values
    )
