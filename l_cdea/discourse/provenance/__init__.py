"""
l_cdea.discourse.provenance — provenance metadata for all discourse knowledge.

Public API:
  attach_provenance(value, provenance, semantic_type="") → ProvenancedValue
  merge_provenance(existing_value, existing_provs, new_value, new_prov) → ProvenanceMergeResult
  validate_provenance(prov) → None  (raises ProvenanceValidationError)
  make_trace_id(source_id, extraction_method, timestamp_index) → str

Types:
  Provenance
  ProvenancedValue
  ProvenanceMergeResult
  ProvenanceTrace
  ProvenanceValidationError
"""
from l_cdea.discourse.provenance.model import (
    Provenance,
    ProvenancedValue,
    ProvenanceMergeResult,
    ProvenanceTrace,
    make_trace_id,
    provenance_to_dict,
    provenance_from_dict,
)
from l_cdea.discourse.provenance.attach import attach_provenance
from l_cdea.discourse.provenance.merge import merge_provenance
from l_cdea.discourse.provenance.validation import (
    validate_provenance,
    ProvenanceValidationError,
)

__all__ = [
    "Provenance",
    "ProvenancedValue",
    "ProvenanceMergeResult",
    "ProvenanceTrace",
    "ProvenanceValidationError",
    "make_trace_id",
    "provenance_to_dict",
    "provenance_from_dict",
    "attach_provenance",
    "merge_provenance",
    "validate_provenance",
]
