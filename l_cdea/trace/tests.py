"""
Trace module tests.

Covers the three validation examples from the spec:
  1. Router + Planner trace — physics COMPUTE_ACCELERATION
  2. Cache hit trace — repeated geography CAPITAL_OF
  3. Fallback trace — unknown input

Additional checks:
  - Deterministic trace IDs (same input → same trace_id)
  - slot_order_used matches slot_key_order(hydrated_slots, arg_order)
  - Sink isolation: InMemoryTraceSink records exact count
  - to_dict / to_json / to_pretty_text do not raise
  - extract_replay_metadata returns all required keys
"""
from __future__ import annotations

from l_cdea.core.parser import parse
from l_cdea.core.router import route_with_trace
from l_cdea.core.planner import plan, cache_result
from l_cdea.core.planner.graph_builder import execute_plan_graph
from l_cdea.discourse import create_discourse_state
from l_cdea.trace import (
    TraceLogger, InMemoryTraceSink,
    to_dict, to_json, to_pretty_text,
    extract_replay_metadata, replay_summary,
    STAGE_ROUTER, STAGE_PLANNER, STAGE_EXECUTION,
)
from l_cdea.core.planner.discourse_lookup import clear_cache

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _run(text: str, state=None, sink=None):
    """Run the fast (planner) path for a query and return (qplan, ptrace, record)."""
    if state is None:
        state = create_discourse_state()

    logger = TraceLogger(text)
    if sink:
        logger.add_sink(sink)

    parsed = parse(text)
    route_result, route_trace = route_with_trace(parsed)

    logger.record_parse(parsed)
    logger.record_router(route_result, route_trace)

    qplan, ptrace = plan(route_result, state)
    logger.record_planner(qplan, ptrace)

    if qplan.is_executable:
        result = execute_plan_graph(qplan.graph)
        if result:
            cache_result(qplan.intent, result)
        # Minimal execution bundle for trace — just node outputs
        class _FakeBundle:
            resolved_graphs = []
            node_outputs = {"0": result} if result else {}
            success_flags = {}
            failures = {}
        logger.record_execution(_FakeBundle())

    record = logger.finalize("success" if not qplan.errors else "failed")
    return qplan, ptrace, record


def test_physics_router_planner_trace():
    """Example 1: physics COMPUTE_ACCELERATION trace."""
    clear_cache()
    text = "calculate acceleration with force 10 N and mass 2 kg"
    qplan, ptrace, record = _run(text)

    # ROUTER stage
    router_evt = next(e for e in record.events if e.stage == STAGE_ROUTER)
    intent = router_evt.payload["selected_intent"]

    ok = intent["domain"] == "physics"
    print(f"{_PASS if ok else _FAIL} router: domain=physics")

    ok = intent["operator_name"] == "COMPUTE_ACCELERATION"
    print(f"{_PASS if ok else _FAIL} router: operator=COMPUTE_ACCELERATION")

    # PLANNER stage
    planner_evt = next(e for e in record.events if e.stage == STAGE_PLANNER)
    p = planner_evt.payload

    ok = p["graph_built"] is True
    print(f"{_PASS if ok else _FAIL} planner: graph_built=True")

    ok = "force" in p["hydrated_slots"] and "mass" in p["hydrated_slots"]
    print(f"{_PASS if ok else _FAIL} planner: force+mass hydrated")

    # slot_order_used must equal sorted keys (V1 alphabetical: force < mass)
    ok = p["slot_order_used"] == ["force", "mass"]
    print(f"{_PASS if ok else _FAIL} planner: slot_order_used=['force','mass'] (alphabetical V1)")

    # retyped slots must carry operator signature types
    ok = p["retyped_slots"].get("force", {}).get("type") is not None
    print(f"{_PASS if ok else _FAIL} planner: retyped_slots present")

    # EXECUTION stage
    exec_evt = next((e for e in record.events if e.stage == STAGE_EXECUTION), None)
    ok = exec_evt is not None
    print(f"{_PASS if ok else _FAIL} execution: stage recorded")
    if exec_evt:
        outputs = exec_evt.payload.get("node_outputs", {})
        ok = len(outputs) > 0
        print(f"{_PASS if ok else _FAIL} execution: output present")


def test_cache_hit_trace():
    """Example 2: repeated query triggers cache hit."""
    clear_cache()
    state = create_discourse_state()
    text = "capital of France"

    # First run — populates cache
    _run(text, state)

    # Second run — should be cache hit
    _, ptrace2, record2 = _run(text, state)

    planner_evt = next(e for e in record2.events if e.stage == STAGE_PLANNER)
    p = planner_evt.payload

    ok = p["cache_hit"] is True
    print(f"{_PASS if ok else _FAIL} cache hit: cache_hit=True on repeat")

    ok = p["graph_built"] is False
    print(f"{_PASS if ok else _FAIL} cache hit: graph_built=False")

    # No EXECUTION stage expected on cache hit
    exec_stages = [e.stage for e in record2.events if e.stage == STAGE_EXECUTION]
    ok = len(exec_stages) == 0
    print(f"{_PASS if ok else _FAIL} cache hit: EXECUTION stage skipped")


def test_fallback_trace():
    """Example 3: unknown input → fallback path."""
    clear_cache()
    text = "unknown phrase with no registered pattern"
    qplan, ptrace, record = _run(text)

    router_evt = next(e for e in record.events if e.stage == STAGE_ROUTER)
    ok = router_evt.payload["fallback_used"] is True
    print(f"{_PASS if ok else _FAIL} fallback: router fallback_used=True")

    planner_evt = next(e for e in record.events if e.stage == STAGE_PLANNER)
    ok = planner_evt.payload["intent"]["fallback"] is True
    print(f"{_PASS if ok else _FAIL} fallback: planner intent.fallback=True")


def test_deterministic_trace_id():
    """Same input + same discourse snapshot → same trace_id."""
    clear_cache()
    from l_cdea.trace import TraceLogger
    t1 = TraceLogger("simplify x + 0", "snap1")
    t2 = TraceLogger("simplify x + 0", "snap1")
    t3 = TraceLogger("simplify x + 0", "snap2")

    ok = t1.trace_id == t2.trace_id
    print(f"{_PASS if ok else _FAIL} determinism: same input+snapshot → same trace_id")

    ok = t1.trace_id != t3.trace_id
    print(f"{_PASS if ok else _FAIL} determinism: different snapshot → different trace_id")


def test_in_memory_sink():
    """InMemoryTraceSink accumulates exactly one record per finalize()."""
    clear_cache()
    sink = InMemoryTraceSink()
    text = "is speeding illegal"
    _run(text, sink=sink)
    _run(text, sink=sink)

    ok = len(sink.records) == 2
    print(f"{_PASS if ok else _FAIL} sink: 2 records after 2 runs")

    ok = sink.latest() is not None
    print(f"{_PASS if ok else _FAIL} sink: latest() returns record")


def test_formatters_do_not_raise():
    """to_dict, to_json, to_pretty_text must not raise on any valid record."""
    clear_cache()
    _, _, record = _run("simplify x + 0")
    try:
        d = to_dict(record)
        assert isinstance(d, dict)
        j = to_json(record)
        assert isinstance(j, str)
        t = to_pretty_text(record)
        assert isinstance(t, str)
        print(f"{_PASS} formatters: to_dict/to_json/to_pretty_text all succeed")
    except Exception as exc:
        print(f"{_FAIL} formatters: {exc}")


def test_replay_metadata_keys():
    """extract_replay_metadata returns all required V1 keys."""
    clear_cache()
    _, _, record = _run("calculate acceleration with force 10 N and mass 2 kg")
    meta = extract_replay_metadata(record)

    required = {
        "original_input", "stage_sequence", "selected_intent",
        "selected_operator", "selected_execution_graph", "final_output",
    }
    missing = required - set(meta.keys())
    ok = not missing
    print(f"{_PASS if ok else _FAIL} replay: all required keys present" +
          (f" (missing: {missing})" if missing else ""))

    ok = meta["selected_operator"] == "physics.COMPUTE_ACCELERATION"
    print(f"{_PASS if ok else _FAIL} replay: selected_operator=physics.COMPUTE_ACCELERATION")

    ok = meta["original_input"] == "calculate acceleration with force 10 N and mass 2 kg"
    print(f"{_PASS if ok else _FAIL} replay: original_input preserved")


def run_all():
    print("\n── Example 1: Physics Router + Planner trace ──────────────────")
    test_physics_router_planner_trace()
    print("\n── Example 2: Cache hit trace ─────────────────────────────────")
    test_cache_hit_trace()
    print("\n── Example 3: Fallback trace ───────────────────────────────────")
    test_fallback_trace()
    print("\n── Deterministic IDs ───────────────────────────────────────────")
    test_deterministic_trace_id()
    print("\n── InMemoryTraceSink ───────────────────────────────────────────")
    test_in_memory_sink()
    print("\n── Formatters ──────────────────────────────────────────────────")
    test_formatters_do_not_raise()
    print("\n── Replay metadata ─────────────────────────────────────────────")
    test_replay_metadata_keys()
    print()


if __name__ == "__main__":
    run_all()
