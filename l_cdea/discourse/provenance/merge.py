"""
merge_provenance(existing_value, existing_provs, new_value, new_prov)
  → ProvenanceMergeResult

Rules:
  1. Identical values  → merge provenance lists (deduplicate, sort by timestamp_index)
  2. Differing values  → conflict=True, return existing provenance unchanged
  3. Provenance list MUST be deduplicated (by trace_id)
  4. Order MUST be deterministic (sorted by timestamp_index, then trace_id)
"""
from __future__ import annotations

from typing import Any, Tuple

from l_cdea.discourse.provenance.model import Provenance, ProvenanceMergeResult


def merge_provenance(
    existing_value: Any,
    existing_provs: Tuple[Provenance, ...],
    new_value: Any,
    new_prov: Provenance,
) -> ProvenanceMergeResult:
    """
    Attempt to merge new_prov into existing_provs.

    If existing_value != new_value: return existing provenance with conflict=True.
    If values match: deduplicate and sort merged provenance list.
    """
    if existing_value != new_value:
        return ProvenanceMergeResult(
            merged_provenance=existing_provs,
            conflict=True,
        )

    seen_ids = {p.trace_id for p in existing_provs}
    if new_prov.trace_id in seen_ids:
        return ProvenanceMergeResult(merged_provenance=existing_provs, conflict=False)

    combined = (*existing_provs, new_prov)
    merged = tuple(sorted(combined, key=lambda p: (p.timestamp_index, p.trace_id)))
    return ProvenanceMergeResult(merged_provenance=merged, conflict=False)
