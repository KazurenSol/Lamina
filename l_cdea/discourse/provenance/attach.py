"""
attach_provenance(value, provenance, semantic_type="") → ProvenancedValue

Rules:
  1. All extracted values MUST be wrapped as ProvenancedValue.
  2. Execution-derived values MUST include execution provenance.
  3. Dataset lookups MUST include dataset provenance.
  4. Parser/router MUST NOT call this — only ingestion/execution layers.
"""
from __future__ import annotations

from typing import Any

from l_cdea.discourse.provenance.model import Provenance, ProvenancedValue
from l_cdea.discourse.provenance.validation import validate_provenance


def attach_provenance(
    value: Any,
    provenance: Provenance,
    semantic_type: str = "",
) -> ProvenancedValue:
    """
    Wrap value with validated provenance.
    Raises ProvenanceValidationError if provenance is invalid.
    """
    validate_provenance(provenance)
    return ProvenancedValue(value=value, semantic_type=semantic_type, provenance=provenance)
