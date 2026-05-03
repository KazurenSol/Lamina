"""
validate_provenance(prov) — raises ProvenanceValidationError on any violation.

Checks:
  1. required fields present and non-empty
  2. source_type is one of the allowed values
  3. confidence within [0.0, 1.0]
  4. trace_id exists
  5. timestamp_index is non-negative
"""
from __future__ import annotations

from l_cdea.discourse.provenance.model import Provenance, VALID_SOURCE_TYPES


class ProvenanceValidationError(Exception):
    pass


def validate_provenance(prov: Provenance) -> None:
    if not prov.source_id:
        raise ProvenanceValidationError("source_id is required and must be non-empty")
    if not prov.source_type:
        raise ProvenanceValidationError("source_type is required and must be non-empty")
    if prov.source_type not in VALID_SOURCE_TYPES:
        raise ProvenanceValidationError(
            f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}, got {prov.source_type!r}"
        )
    if not prov.extraction_method:
        raise ProvenanceValidationError("extraction_method is required and must be non-empty")
    if not (0.0 <= prov.confidence <= 1.0):
        raise ProvenanceValidationError(
            f"confidence must be in [0.0, 1.0], got {prov.confidence}"
        )
    if not prov.trace_id:
        raise ProvenanceValidationError("trace_id is required and must be non-empty")
    if prov.timestamp_index < 0:
        raise ProvenanceValidationError(
            f"timestamp_index must be non-negative, got {prov.timestamp_index}"
        )
