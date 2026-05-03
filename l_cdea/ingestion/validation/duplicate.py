"""
detect_duplicate(value, state) → Optional[str]

Returns the node_id of the first matching duplicate, or None.

Detection order:
  1. Exact match: same Python value already in discourse
  2. Canonical match: same string after strip+lower (catches casing/whitespace variants)
  3. Dataset match: same source_id + same value in provenance
"""
from __future__ import annotations

from typing import Optional

from l_cdea.discourse.provenance.model import ProvenancedValue
from l_cdea.discourse.state import DiscourseState


def detect_duplicate(
    value: ProvenancedValue,
    state: DiscourseState,
) -> Optional[str]:
    target = value.value

    for node in state.nodes.values():
        # 1. Exact match
        if node.value == target:
            return node.id

    # 2. Canonical match (string normalization)
    if isinstance(target, str):
        norm_target = target.strip().lower()
        for node in state.nodes.values():
            if isinstance(node.value, str) and node.value.strip().lower() == norm_target:
                return node.id

    # 3. Dataset match: same dataset source_id produced this value
    new_source_id = value.provenance.source_id
    if new_source_id:
        for node in state.nodes.values():
            if node.value == target:
                continue  # already caught above
            for prov in node.provenance:
                if prov.source_id == new_source_id and node.value == target:
                    return node.id

    return None
