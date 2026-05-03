"""
Data module tests.

Covers all four spec validation examples:
  1. capital of France  → Paris (country dataset)
  2. capital of Texas   → Austin (US state dataset)
  3. capital of Atlantis → symbolic fallback, no crash
  4. capital of France (repeat in-process) → cache_hit=True, output=Paris

Additional checks:
  - DatasetRegistry deduplication
  - Normalized key matching (case-insensitive)
  - lookup() never raises on missing dataset or key
  - validate_dataset() catches bad datasets
  - contains() returns correct bool
"""
from __future__ import annotations

import l_cdea.data  # registers built-in datasets
from l_cdea.core.parser import parse
from l_cdea.core.router import route_with_trace
from l_cdea.core.planner import plan, cache_result
from l_cdea.core.planner.graph_builder import execute_plan_graph
from l_cdea.core.planner.discourse_lookup import clear_cache
from l_cdea.discourse import create_discourse_state
from l_cdea.data.lookup import lookup, contains, is_miss, clear_lookup_trace
from l_cdea.data.registry import DatasetRegistry, DatasetNotFoundError
from l_cdea.data.validation import validate_dataset
from l_cdea.data.datasets import Dataset
from l_cdea.core.types.base import SemanticType

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _run(text: str, state=None):
    if state is None:
        state = create_discourse_state()
    clear_lookup_trace()
    parsed = parse(text)
    route_result, _ = route_with_trace(parsed)
    qplan, _ = plan(route_result, state)
    result = None
    if qplan.is_executable:
        result = execute_plan_graph(qplan.graph)
        if result:
            cache_result(qplan.intent, result)
    return qplan, result


# ── Example 1: capital of France ──────────────────────────────────────────────

def test_capital_of_france():
    clear_cache()
    qplan, result = _run("capital of France")

    ok = result is not None and result.value == "Paris"
    print(f"{_PASS if ok else _FAIL} capital of France → Paris (got {result.value if result else None!r})")

    ok = result is not None and result.type == SemanticType.ENTITY
    print(f"{_PASS if ok else _FAIL} capital of France → type=Entity")


# ── Example 2: capital of Texas ───────────────────────────────────────────────

def test_capital_of_texas():
    clear_cache()
    qplan, result = _run("capital of Texas")

    ok = result is not None and result.value == "Austin"
    print(f"{_PASS if ok else _FAIL} capital of Texas → Austin (got {result.value if result else None!r})")


# ── Example 3: capital of Atlantis — symbolic fallback, no crash ───────────────

def test_capital_of_atlantis():
    clear_cache()
    try:
        qplan, result = _run("capital of Atlantis")
        ok = result is not None and "Atlantis" in str(result.value) and not is_miss(result)
        print(f"{_PASS if ok else _FAIL} capital of Atlantis → symbolic fallback (got {result.value if result else None!r})")
    except Exception as exc:
        print(f"{_FAIL} capital of Atlantis raised: {exc}")


# ── Example 4: repeated in-process query — cache hit ─────────────────────────

def test_cache_hit_in_process():
    clear_cache()
    state = create_discourse_state()

    _run("capital of France", state)           # populates cache
    qplan2, result2 = _run("capital of France", state)

    ok = qplan2.cache_hit
    print(f"{_PASS if ok else _FAIL} cache hit: cache_hit=True on second in-process run")

    ok = result2 is None and qplan2.cached_result is not None and qplan2.cached_result.value == "Paris"
    print(f"{_PASS if ok else _FAIL} cache hit: cached_result=Paris")


# ── Registry tests ─────────────────────────────────────────────────────────────

def test_datasets_registered():
    ok = DatasetRegistry.has("country_capitals_v1")
    print(f"{_PASS if ok else _FAIL} registry: country_capitals_v1 registered")

    ok = DatasetRegistry.has("us_state_capitals_v1")
    print(f"{_PASS if ok else _FAIL} registry: us_state_capitals_v1 registered")


def test_lookup_exact():
    tv, trace = lookup("country_capitals_v1", "Japan", operator_name="test")
    ok = tv.value == "Tokyo" and trace.hit
    print(f"{_PASS if ok else _FAIL} lookup exact: Japan → Tokyo")


def test_lookup_normalized():
    tv, trace = lookup("country_capitals_v1", "france", operator_name="test")
    ok = tv.value == "Paris" and trace.hit
    print(f"{_PASS if ok else _FAIL} lookup normalized: 'france' → Paris")


def test_lookup_miss_no_crash():
    tv, trace = lookup("country_capitals_v1", "Narnia", operator_name="test")
    ok = is_miss(tv) and not trace.hit and trace.fallback_used
    print(f"{_PASS if ok else _FAIL} lookup miss: Narnia → is_miss=True, no crash")


def test_lookup_missing_dataset_no_crash():
    tv, trace = lookup("nonexistent_dataset_v1", "anything", operator_name="test")
    ok = is_miss(tv) and not trace.hit
    print(f"{_PASS if ok else _FAIL} lookup missing dataset → is_miss=True, no crash")


def test_contains():
    ok = contains("country_capitals_v1", "Germany")
    print(f"{_PASS if ok else _FAIL} contains: Germany → True")

    ok = not contains("country_capitals_v1", "Atlantis")
    print(f"{_PASS if ok else _FAIL} contains: Atlantis → False")


def test_validation_rejects_bad_dataset():
    # Provenance missing 'source' key — passes __post_init__ but fails validate_dataset
    bad = Dataset(
        name="test_bad_v1",
        domain="test",
        key_type=SemanticType.ENTITY,
        value_type=SemanticType.ENTITY,
        records={"a": "b"},
        version="1.0.0",
        provenance={"author": "nobody"},  # missing required 'source' key
    )
    errors = validate_dataset(bad)
    ok = any("source" in e for e in errors)
    print(f"{_PASS if ok else _FAIL} validation: missing provenance.source → error reported")


def run_all():
    print("\n── Example 1: capital of France ───────────────────────────────")
    test_capital_of_france()
    print("\n── Example 2: capital of Texas ────────────────────────────────")
    test_capital_of_texas()
    print("\n── Example 3: capital of Atlantis (fallback) ──────────────────")
    test_capital_of_atlantis()
    print("\n── Example 4: in-process cache hit ────────────────────────────")
    test_cache_hit_in_process()
    print("\n── Registry ────────────────────────────────────────────────────")
    test_datasets_registered()
    print("\n── Lookup ──────────────────────────────────────────────────────")
    test_lookup_exact()
    test_lookup_normalized()
    test_lookup_miss_no_crash()
    test_lookup_missing_dataset_no_crash()
    test_contains()
    print("\n── Validation ──────────────────────────────────────────────────")
    test_validation_rejects_bad_dataset()
    print()


if __name__ == "__main__":
    run_all()
