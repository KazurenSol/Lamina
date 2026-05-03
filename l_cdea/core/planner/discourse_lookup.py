"""
Discourse-first lookup: check DiscourseState for a cached result before building any graph.

Two-layer strategy (V1):
  Layer 1 — planner result cache  (in-session Dict[key → TypedValue])
  Layer 2 — discourse node scan   (DiscourseState node graph)

Authority rule:
  DiscourseState is the authoritative memory layer.
  The planner cache is an optimization layer only.
  If both layers have a value for the same key and they disagree,
  the DiscourseState value wins and the planner cache is reconciled.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from l_cdea.core.types.base import TypedValue
from l_cdea.core.router.intent import IntentFrame
from l_cdea.core.planner.plan import DiscourseLookupResult
from l_cdea.discourse.state import DiscourseState
from l_cdea.discourse.memory_graph import lookup_by_value


# In-session result cache — optimization only, not authoritative
_RESULT_CACHE: Dict[str, TypedValue] = {}


def make_lookup_key(intent: IntentFrame) -> str:
    """
    Canonical, deterministic key for an intent.
    Same domain + operator + sorted slots → same key.
    """
    slot_part = ":".join(f"{k}={v}" for k, v in sorted(intent.slots.items()))
    return f"{intent.domain}.{intent.operator_name}:{slot_part}"


def cache_result(intent: IntentFrame, result: TypedValue) -> None:
    """Store a result after successful execution so future identical queries hit cache."""
    key = make_lookup_key(intent)
    _RESULT_CACHE[key] = result


def clear_cache() -> None:
    _RESULT_CACHE.clear()


def discourse_lookup(
    intent: IntentFrame,
    state: DiscourseState,
) -> DiscourseLookupResult:
    """
    Check for a cached result. Returns hit=True if found.

    Layer 1 — planner result cache (optimization):
      Fast O(1) lookup. On a hit, the cached value is verified against
      DiscourseState. If DiscourseState holds the same value, return it
      as authoritative. If DiscourseState holds a different value,
      DiscourseState wins: the cache entry is reconciled and the discourse
      value is returned. If DiscourseState has no entry, the cache value
      is returned as a non-authoritative optimization hit.

    Layer 2 — discourse node scan (authoritative):
      Scans DiscourseState for stored query-key marker nodes.
    """
    key = make_lookup_key(intent)
    checked: Tuple[str, ...] = (key,)

    # ── Layer 1: planner cache hit ─────────────────────────────────────────
    if key in _RESULT_CACHE:
        cached = _RESULT_CACHE[key]

        # Verify against DiscourseState (authoritative layer)
        discourse_node = lookup_by_value(state, cached.value)
        if discourse_node is not None:
            authoritative = TypedValue(
                value=discourse_node.value,
                type=discourse_node.semantic_type,
            )
            if authoritative != cached:
                # DiscourseState disagrees — reconcile cache to authoritative value
                _RESULT_CACHE[key] = authoritative

            return DiscourseLookupResult(
                hit=True,
                value=authoritative,
                checked_keys=checked,
                match_strategy="planner_cache+discourse_verified",
            )

        # DiscourseState has no entry for this value — cache is an optimization hint.
        # Return the cached value; discourse may not have persisted it yet.
        return DiscourseLookupResult(
            hit=True,
            value=cached,
            checked_keys=checked,
            match_strategy="planner_cache",
        )

    # ── Layer 2: discourse node scan ───────────────────────────────────────
    marker_value = {"_query_key": key}
    marker_node = lookup_by_value(state, marker_value)
    if marker_node is not None:
        result_key = f"_result:{key}"
        result_node = lookup_by_value(state, {"_result_key": result_key})
        if result_node is not None:
            from l_cdea.core.types.base import SemanticType
            tv = TypedValue(result_node.value, result_node.semantic_type)
            # Populate cache so subsequent lookups are O(1)
            _RESULT_CACHE[key] = tv
            return DiscourseLookupResult(
                hit=True,
                value=tv,
                checked_keys=checked,
                match_strategy="discourse_node_scan",
            )

    return DiscourseLookupResult(
        hit=False,
        value=None,
        checked_keys=checked,
        match_strategy="none",
    )
