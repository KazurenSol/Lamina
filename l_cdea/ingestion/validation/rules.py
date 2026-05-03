"""
apply_rules(value, duplicate_of, conflict_with, score) → ValidationDecision

Decision priority (first match wins):
  1. conflict  — conflicting knowledge MUST NOT overwrite
  2. merge     — duplicate detected; merge provenance, reinforce salience
  3. reject    — score below threshold; low-quality knowledge excluded
  4. accept    — passes all checks

Threshold: 0.5  (scores below this are rejected)
Rules MUST be deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from l_cdea.discourse.provenance.model import ProvenancedValue

REJECT_THRESHOLD: float = 0.5

VALID_STATUSES = frozenset({"accept", "reject", "merge", "conflict"})


@dataclass(frozen=True)
class ValidationDecision:
    status: str                    # "accept" | "reject" | "merge" | "conflict"
    reason: str
    score: float
    duplicate_of: Optional[str]    # node_id if merge
    conflict_with: Optional[str]   # node_id if conflict

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid validation status: {self.status!r}")


@dataclass(frozen=True)
class ValidatedKnowledge:
    value: ProvenancedValue
    decision: ValidationDecision


def apply_rules(
    value: ProvenancedValue,
    duplicate_of: Optional[str],
    conflict_with: Optional[str],
    score: float,
) -> ValidationDecision:
    if conflict_with is not None:
        return ValidationDecision(
            status="conflict",
            reason=f"conflicts with existing node '{conflict_with}'",
            score=score,
            duplicate_of=None,
            conflict_with=conflict_with,
        )
    if duplicate_of is not None:
        return ValidationDecision(
            status="merge",
            reason=f"duplicate of existing node '{duplicate_of}'",
            score=score,
            duplicate_of=duplicate_of,
            conflict_with=None,
        )
    if score < REJECT_THRESHOLD:
        return ValidationDecision(
            status="reject",
            reason=f"quality score {score:.3f} below threshold {REJECT_THRESHOLD}",
            score=score,
            duplicate_of=None,
            conflict_with=None,
        )
    return ValidationDecision(
        status="accept",
        reason="passed all validation rules",
        score=score,
        duplicate_of=None,
        conflict_with=None,
    )
