"""
Discourse persistence tests.

Covers all four spec validation examples:
  1. Cross-process cache hit (save → fresh load → query → cache_hit=True)
  2. Deterministic save (same state → identical file bytes)
  3. Empty startup (no file → empty DiscourseState, no crash)
  4. Corrupt file → PersistenceError, no overwrite
"""
from __future__ import annotations

import json
import os
import tempfile

import l_cdea.data  # registers built-in datasets
from l_cdea.core.parser import parse
from l_cdea.core.router import route_with_trace
from l_cdea.core.planner import plan, cache_result
from l_cdea.core.planner.discourse_lookup import _RESULT_CACHE, clear_cache
from l_cdea.core.planner.graph_builder import execute_plan_graph
from l_cdea.discourse import (
    create_discourse_state, update_discourse,
    save_state, load_state, snapshot_id,
    PersistenceError,
)
from l_cdea.discourse.storage import state_to_snapshot, snapshot_to_state

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _run_query(text: str, state):
    """Run one query against state, return (qplan, result). Updates discourse state."""
    from l_cdea.discourse import update_discourse
    parsed = parse(text)
    route_result, _ = route_with_trace(parsed)
    qplan, _ = plan(route_result, state)
    result = None
    if qplan.is_executable:
        result = execute_plan_graph(qplan.graph)
        if result:
            cache_result(qplan.intent, result)
            # Update discourse so state actually changes (enables persistence tests)
            class _Bundle:
                resolved_graphs = [qplan.graph]
                node_outputs = {"0": result}
                success_flags = {"0": True}
                failures = {}
            update_discourse(_Bundle(), state)
    return qplan, result


# ── Example 1: cross-process cache hit ─────────────────────────────────────────

def test_cross_process_cache_hit():
    """Save after first run → load in fresh process → second run hits cache."""
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)  # remove so load_state sees a missing file first

    try:
        # === Process 1 ===
        state1 = load_state(path)          # empty — file does not exist
        ok = len(state1.nodes) == 0
        print(f"{_PASS if ok else _FAIL} cross-process: empty state on first load")

        qplan1, result1 = _run_query("capital of France", state1)
        ok = result1 is not None and result1.value == "Paris"
        print(f"{_PASS if ok else _FAIL} cross-process: first run returns Paris")

        save_state(state1, path)
        ok = os.path.exists(path)
        print(f"{_PASS if ok else _FAIL} cross-process: state file created")

        # === Process 2: simulate fresh process ===
        clear_cache()  # wipes _RESULT_CACHE as a new process would

        state2 = load_state(path)          # restores DiscourseState + planner cache
        ok = bool(_RESULT_CACHE)           # planner cache should be restored
        print(f"{_PASS if ok else _FAIL} cross-process: planner cache restored after load")

        qplan2, result2 = _run_query("capital of France", state2)
        ok = qplan2.cache_hit
        print(f"{_PASS if ok else _FAIL} cross-process: cache_hit=True on second run")

        ok = qplan2.cached_result is not None and qplan2.cached_result.value == "Paris"
        print(f"{_PASS if ok else _FAIL} cross-process: cached_result=Paris")

    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── Example 2: deterministic save ─────────────────────────────────────────────

def test_deterministic_save():
    """Same state saved twice → identical file bytes."""
    clear_cache()
    state = create_discourse_state()
    _run_query("capital of France", state)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as a:
        path_a = a.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as b:
        path_b = b.name

    try:
        save_state(state, path_a)
        save_state(state, path_b)

        with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
            ok = fa.read() == fb.read()
        print(f"{_PASS if ok else _FAIL} deterministic save: identical file bytes")
    finally:
        for p in (path_a, path_b):
            if os.path.exists(p):
                os.unlink(p)


# ── Example 3: empty startup ───────────────────────────────────────────────────

def test_empty_startup():
    """load_state on non-existent path returns empty DiscourseState, no crash."""
    clear_cache()
    path = "/tmp/__l_cdea_nonexistent_state_xyz__.json"
    if os.path.exists(path):
        os.unlink(path)
    try:
        state = load_state(path)
        ok = len(state.nodes) == 0 and len(state.edges) == 0 and state.temporal_index == 0
        print(f"{_PASS if ok else _FAIL} empty startup: empty DiscourseState, no crash")
    except Exception as exc:
        print(f"{_FAIL} empty startup raised: {exc}")


# ── Example 4: corrupt file → PersistenceError ────────────────────────────────

def test_corrupt_file():
    """Invalid JSON → PersistenceError; file must not be overwritten."""
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
        f.write("THIS IS NOT JSON {{{")

    original_content = open(path).read()

    try:
        load_state(path)
        print(f"{_FAIL} corrupt file: should have raised PersistenceError")
    except PersistenceError:
        print(f"{_PASS} corrupt file: PersistenceError raised")
        # File must not have been overwritten
        ok = open(path).read() == original_content
        print(f"{_PASS if ok else _FAIL} corrupt file: original file not overwritten")
    except Exception as exc:
        print(f"{_FAIL} corrupt file: wrong exception type: {type(exc).__name__}: {exc}")
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── snapshot_id stability ──────────────────────────────────────────────────────

def test_snapshot_id_stability():
    """Same state → same snapshot_id. Different state → different snapshot_id."""
    clear_cache()
    s1 = create_discourse_state()
    s2 = create_discourse_state()

    ok = snapshot_id(s1) == snapshot_id(s2)
    print(f"{_PASS if ok else _FAIL} snapshot_id: two empty states → same id")

    _run_query("capital of Spain", s1)
    ok = snapshot_id(s1) != snapshot_id(s2)
    print(f"{_PASS if ok else _FAIL} snapshot_id: populated state ≠ empty state")


# ── Round-trip ─────────────────────────────────────────────────────────────────

def test_round_trip():
    """state_to_snapshot → snapshot_to_state preserves nodes, edges, temporal_index."""
    clear_cache()
    state = create_discourse_state()
    _run_query("capital of Japan", state)

    snap = state_to_snapshot(state)
    restored = snapshot_to_state(snap)

    ok = len(restored.nodes) == len(state.nodes)
    print(f"{_PASS if ok else _FAIL} round-trip: node count preserved ({len(state.nodes)})")

    ok = len(restored.edges) == len(state.edges)
    print(f"{_PASS if ok else _FAIL} round-trip: edge count preserved ({len(state.edges)})")

    ok = restored.temporal_index == state.temporal_index
    print(f"{_PASS if ok else _FAIL} round-trip: temporal_index preserved ({state.temporal_index})")


# ── Cache authority tamper test ───────────────────────────────────────────────

def test_planner_cache_cannot_override_discourse_state():
    """
    DiscourseState is authoritative. A tampered planner_cache entry in the saved JSON
    must be ignored or repaired — the output must still come from DiscourseState.

    Steps:
    1. Run 'capital of France' → expect Paris, save state
    2. Corrupt planner_cache in the JSON file (France → WrongCity)
    3. Load state — cache should be reconciled against DiscourseState
    4. Run query again → output must be Paris; cache value must be repaired
    """
    import l_cdea.domain  # ensure operators + governance registered
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    try:
        # ── Step 1: Run and save ──────────────────────────────────────────
        state = create_discourse_state()
        _run_query("capital of France", state)
        save_state(state, state_path)

        # Verify saved file has discourse nodes
        with open(state_path) as fh:
            saved = json.load(fh)
        has_paris = any(
            n.get("value") == "Paris"
            for n in saved.get("nodes", [])
        )
        ok = has_paris
        print(f"{_PASS if ok else _FAIL} saved state contains DiscourseState node with value='Paris'")

        # ── Step 2: Corrupt planner_cache in JSON ────────────────────────
        for key in saved.get("metadata", {}).get("planner_cache", {}):
            saved["metadata"]["planner_cache"][key]["value"] = "WrongCity"
        with open(state_path, "w") as fh:
            json.dump(saved, fh)

        tampered_count = len(saved.get("metadata", {}).get("planner_cache", {}))
        print(f"  (tampered {tampered_count} cache entries → 'WrongCity')")

        # ── Step 3: Load state — tampered cache entry is dropped ─────────────
        clear_cache()
        loaded_state = load_state(state_path)

        # Tampered entry (WrongCity) is not in DiscourseState → dropped at load
        wrongcity_in_cache = any(v.value == "WrongCity" for v in _RESULT_CACHE.values())
        ok = not wrongcity_in_cache
        print(f"{_PASS if ok else _FAIL} after load: tampered 'WrongCity' is not in cache (dropped)")

        # ── Step 4: Run query — must return Paris (re-executes since cache dropped) ─
        qplan, result = _run_query("capital of France", loaded_state)
        ok = result is not None and result.value == "Paris"
        print(f"{_PASS if ok else _FAIL} post-load query returns 'Paris' (got {result.value if result else None!r})")

        # ── Step 5: Cache now repaired — Paris in cache, WrongCity absent ───
        paris_in_cache = any(v.value == "Paris" for v in _RESULT_CACHE.values())
        wrongcity_in_cache = any(v.value == "WrongCity" for v in _RESULT_CACHE.values())
        ok = paris_in_cache and not wrongcity_in_cache
        print(f"{_PASS if ok else _FAIL} cache repaired after re-execution (Paris={paris_in_cache}, WrongCity={wrongcity_in_cache})")

    finally:
        os.unlink(state_path)


def run_all():
    print("\n── Example 1: Cross-process cache hit ─────────────────────────")
    test_cross_process_cache_hit()
    print("\n── Example 2: Deterministic save ──────────────────────────────")
    test_deterministic_save()
    print("\n── Example 3: Empty startup ────────────────────────────────────")
    test_empty_startup()
    print("\n── Example 4: Corrupt file ─────────────────────────────────────")
    test_corrupt_file()
    print("\n── snapshot_id stability ───────────────────────────────────────")
    test_snapshot_id_stability()
    print("\n── Round-trip serialization ────────────────────────────────────")
    test_round_trip()
    print("\n── Cache authority tamper test ─────────────────────────────────")
    test_planner_cache_cannot_override_discourse_state()
    print()


if __name__ == "__main__":
    run_all()
