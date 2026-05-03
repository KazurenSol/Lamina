"""
Deterministic data lookup.

Strategy (in order):
  1. Exact key match
  2. Normalized match (strip + lowercase)
  3. Miss → LookupMiss TypedValue, no crash

Trace state:
  Module-level _last_trace stores the most recent DataLookupTrace.
  run.py reads it after execute_plan_graph() via get_last_lookup_trace().
  Call clear_lookup_trace() before each query to avoid stale data.

Rules:
- No fuzzy matching in V1.
- Missing key never raises; returns a LookupMiss TypedValue.
- Operators that call lookup() record their own operator_name.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from l_cdea.core.types.base import TypedValue, SemanticType
from l_cdea.data.registry import DatasetRegistry, DatasetNotFoundError

# Sentinel value stored in TypedValue when lookup fails
LOOKUP_MISS_PREFIX = "__lookup_miss__"


@dataclass
class DataLookupTrace:
    """Record of a single data-backed lookup call."""
    operator_name: str
    dataset_name: str
    lookup_key: str
    hit: bool
    returned_value: Any
    fallback_used: bool
    provenance: Dict = field(default_factory=dict)


# Module-level trace slot — one per query (latest lookup wins)
_last_trace: Optional[DataLookupTrace] = None
# Accumulate all traces from a single query for multi-dataset operators
_trace_log: list = []


def lookup(
    dataset_name: str,
    key: str,
    operator_name: str = "unknown",
) -> Tuple[TypedValue, DataLookupTrace]:
    """
    Look up key in the named dataset.

    Returns (TypedValue, DataLookupTrace).
    On miss, TypedValue.value starts with LOOKUP_MISS_PREFIX.
    Never raises.
    """
    global _last_trace

    try:
        ds = DatasetRegistry.get(dataset_name)
    except DatasetNotFoundError:
        tv = TypedValue(value=f"{LOOKUP_MISS_PREFIX}:{dataset_name}:{key}", type=SemanticType.ENTITY)
        trace = DataLookupTrace(
            operator_name=operator_name,
            dataset_name=dataset_name,
            lookup_key=key,
            hit=False,
            returned_value=None,
            fallback_used=True,
            provenance={"error": "dataset_not_found"},
        )
        _last_trace = trace
        _trace_log.append(trace)
        return tv, trace

    # 1. Exact match
    value = ds.get(key)
    if value is not None:
        tv = TypedValue(value=value, type=ds.value_type)
        trace = DataLookupTrace(
            operator_name=operator_name,
            dataset_name=dataset_name,
            lookup_key=key,
            hit=True,
            returned_value=value,
            fallback_used=False,
            provenance=ds.provenance,
        )
        _last_trace = trace
        _trace_log.append(trace)
        return tv, trace

    # 2. Normalized match
    value = ds.get_normalized(key)
    if value is not None:
        tv = TypedValue(value=value, type=ds.value_type)
        trace = DataLookupTrace(
            operator_name=operator_name,
            dataset_name=dataset_name,
            lookup_key=key,
            hit=True,
            returned_value=value,
            fallback_used=False,
            provenance={**ds.provenance, "match_strategy": "normalized"},
        )
        _last_trace = trace
        _trace_log.append(trace)
        return tv, trace

    # 3. Miss
    tv = TypedValue(value=f"{LOOKUP_MISS_PREFIX}:{dataset_name}:{key}", type=ds.value_type)
    trace = DataLookupTrace(
        operator_name=operator_name,
        dataset_name=dataset_name,
        lookup_key=key,
        hit=False,
        returned_value=None,
        fallback_used=True,
        provenance=ds.provenance,
    )
    _last_trace = trace
    _trace_log.append(trace)
    return tv, trace


def contains(dataset_name: str, key: str) -> bool:
    """Return True if key has an exact or normalized match in the dataset."""
    try:
        ds = DatasetRegistry.get(dataset_name)
    except DatasetNotFoundError:
        return False
    return ds.get(key) is not None or ds.get_normalized(key) is not None


def is_miss(tv: TypedValue) -> bool:
    """True if TypedValue represents a lookup miss."""
    return isinstance(tv.value, str) and tv.value.startswith(LOOKUP_MISS_PREFIX)


def get_last_lookup_trace() -> Optional[DataLookupTrace]:
    return _last_trace


def get_all_lookup_traces() -> list:
    return list(_trace_log)


def clear_lookup_trace() -> None:
    global _last_trace
    _last_trace = None
    _trace_log.clear()
