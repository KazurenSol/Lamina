"""
l_cdea.ingestion.validation — knowledge gatekeeper before DiscourseState.

Public API:
  validate(value, state)            → ValidationDecision
  validate_with_trace(value, state) → (ValidationDecision, ValidationTrace)
  validate_batch(values, state)     → Tuple[ValidatedKnowledge, ...]

Types:
  ValidationDecision
  ValidatedKnowledge
  ValidationTrace
"""
from l_cdea.ingestion.validation.validate import validate, validate_with_trace, validate_batch
from l_cdea.ingestion.validation.rules import ValidationDecision, ValidatedKnowledge, REJECT_THRESHOLD
from l_cdea.ingestion.validation.trace import ValidationTrace
from l_cdea.ingestion.validation.scoring import compute_score
from l_cdea.ingestion.validation.duplicate import detect_duplicate
from l_cdea.ingestion.validation.conflict import detect_conflict

__all__ = [
    "validate",
    "validate_with_trace",
    "validate_batch",
    "ValidationDecision",
    "ValidatedKnowledge",
    "ValidationTrace",
    "compute_score",
    "detect_duplicate",
    "detect_conflict",
    "REJECT_THRESHOLD",
]
