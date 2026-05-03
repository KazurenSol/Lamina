"""
detect_conflict(value, state) → Optional[str]

Returns the node_id of the first conflicting node, or None.

V1 conflict detection — same extraction context, different value:
  A conflict exists when an existing node was extracted from the same
  source+chunk+method as the new value but holds a different value.
  This catches cases like "CAPITAL_OF(France) = Paris" vs "CAPITAL_OF(France) = Lyon"
  when both share the same source document, chunk, and extraction method.

A node that exactly matches the new value is never a conflict (it's a duplicate).
"""
from __future__ import annotations

from typing import Optional

from l_cdea.discourse.provenance.model import ProvenancedValue
from l_cdea.discourse.state import DiscourseState


def detect_conflict(
    value: ProvenancedValue,
    state: DiscourseState,
) -> Optional[str]:
    new_source_id = value.provenance.source_id
    new_chunk_id = value.provenance.chunk_id
    new_method = value.provenance.extraction_method

    # chunk_id is required to pin down the extraction context for conflict detection
    if not new_chunk_id:
        return None

    for node in state.nodes.values():
        if node.value == value.value:
            continue  # same value → duplicate, not conflict

        for prov in node.provenance:
            if (prov.source_id == new_source_id
                    and prov.chunk_id == new_chunk_id
                    and prov.extraction_method == new_method):
                return node.id

    return None
