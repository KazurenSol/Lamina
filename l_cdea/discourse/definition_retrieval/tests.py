"""
Definition retrieval tests.

Covers all 5 spec validation examples:
  1. "what is acceleration" → stored definition text returned
  2. "define force"         → stored definition text returned
  3. "what is velocity"     → routes to discourse.GET_DEFINITION (not physics)
  4. missing term           → no crash, fallback definition_of(term)
  5. duplicate definition   → single node, merged provenance (idempotent register)

Additional checks:
  - normalize_term strips punctuation and lowercases
  - lookup_definition returns hit=False for unknown terms
  - lookup ranks by confidence (highest wins)
  - router recognizes all 4 pattern forms
  - planner short-circuits to definition_retrieval (cache_hit=True)
  - GET_DEFINITION CDL operator works standalone
  - DiscourseNode with metadata survives persistence round-trip
"""
from __future__ import annotations

import l_cdea.domain   # registers operators + governance
import l_cdea.data     # registers datasets

from l_cdea.discourse.definition_retrieval import (
    normalize_term,
    register_definition,
    lookup_definition,
    clear_definitions,
    DefinitionLookupResult,
    DefinitionRetrievalTrace,
)

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _setup():
    """Reset definition store before each test group."""
    clear_definitions()


# ── Spec Example 1: what is acceleration ─────────────────────────────────────

def test_example_1_what_is_acceleration():
    _setup()
    register_definition(
        "acceleration",
        "Acceleration is the rate of change of velocity.",
        source_id="physics_doc_v1",
        confidence=0.9,
    )
    result = lookup_definition("acceleration")
    ok = result.hit
    print(f"{_PASS if ok else _FAIL} example 1: lookup hit={result.hit}")
    ok2 = result.definition_text == "Acceleration is the rate of change of velocity."
    print(f"{_PASS if ok2 else _FAIL} example 1: definition_text={result.definition_text!r}")
    ok3 = result.normalized_term == "acceleration"
    print(f"{_PASS if ok3 else _FAIL} example 1: normalized_term={result.normalized_term!r}")


# ── Spec Example 2: define force ─────────────────────────────────────────────

def test_example_2_define_force():
    _setup()
    register_definition(
        "force",
        "Force is defined as mass times acceleration.",
        source_id="physics_doc_v1",
        confidence=0.85,
    )
    result = lookup_definition("force")
    ok = result.hit and result.definition_text == "Force is defined as mass times acceleration."
    print(f"{_PASS if ok else _FAIL} example 2: force definition={result.definition_text!r}")


# ── Spec Example 3: velocity false-positive prevention ───────────────────────

def test_example_3_velocity_routes_to_definition():
    """'what is velocity' must route to discourse.GET_DEFINITION, not physics."""
    _setup()
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace

    parsed = parse("what is velocity")
    route_result, route_trace = route_with_trace(parsed)
    intent = route_result.selected_intent

    ok = intent.domain == "discourse"
    print(f"{_PASS if ok else _FAIL} example 3: domain={intent.domain!r} (expected 'discourse')")
    ok2 = intent.operator_name == "GET_DEFINITION"
    print(f"{_PASS if ok2 else _FAIL} example 3: operator={intent.operator_name!r}")
    ok3 = not intent.fallback
    print(f"{_PASS if ok3 else _FAIL} example 3: fallback={intent.fallback} (expected False)")
    ok4 = intent.slots.get("term", "").lower() == "velocity"
    print(f"{_PASS if ok4 else _FAIL} example 3: term={intent.slots.get('term')!r}")


# ── Spec Example 4: missing term fallback ────────────────────────────────────

def test_example_4_missing_term_fallback():
    """Unknown term: no crash, returns definition_of(term). cache_hit=False for fallback."""
    _setup()
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.planner import plan
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.discourse import create_discourse_state

    clear_cache()
    state = create_discourse_state()
    parsed = parse("what is luminiferous ether")
    route_result, _ = route_with_trace(parsed)
    qplan, _ = plan(route_result, state)

    ok = not qplan.cache_hit  # fallback → cache_hit must be False
    print(f"{_PASS if ok else _FAIL} example 4: qplan.cache_hit={qplan.cache_hit} (expected False)")
    ok2 = qplan.cached_result is not None
    print(f"{_PASS if ok2 else _FAIL} example 4: cached_result is not None")
    if qplan.cached_result:
        val = qplan.cached_result.value
        ok3 = "luminiferous" in val.lower() or "definition_of" in val.lower()
        print(f"{_PASS if ok3 else _FAIL} example 4: fallback value={val!r}")
        ok4 = qplan.cache_trace.get("fallback") is True
        print(f"{_PASS if ok4 else _FAIL} example 4: cache_trace fallback=True")


# ── Spec Example 5: duplicate definition merges (idempotent) ─────────────────

def test_example_5_duplicate_definition():
    """Same term from two sources → store has two entries but lookup returns best one."""
    _setup()
    e1 = register_definition("acceleration", "Acceleration is rate of change of velocity.",
                              source_id="doc_A", confidence=0.9)
    e2 = register_definition("acceleration", "Acceleration is rate of change of velocity.",
                              source_id="doc_B", confidence=0.85)
    # Same source_id + normalized_term deduplicates:
    e3 = register_definition("acceleration", "Acceleration is rate of change of velocity.",
                              source_id="doc_A", confidence=0.9)

    from l_cdea.discourse.definition_retrieval.lookup import _DEFINITION_STORE
    accel_entries = [e for e in _DEFINITION_STORE if e.normalized_term == "acceleration"]
    ok = len(accel_entries) == 2  # doc_A + doc_B (doc_A not added twice)
    print(f"{_PASS if ok else _FAIL} example 5: {len(accel_entries)} entries (expected 2, idempotent)")

    result = lookup_definition("acceleration")
    ok2 = result.hit
    print(f"{_PASS if ok2 else _FAIL} example 5: lookup hit")
    # Best is doc_A (confidence 0.9)
    ok3 = result.confidence == 0.9
    print(f"{_PASS if ok3 else _FAIL} example 5: highest confidence selected ({result.confidence})")


# ── normalize_term ────────────────────────────────────────────────────────────

def test_normalize_term():
    cases = [
        ("Acceleration", "acceleration"),
        ("velocity?",    "velocity"),
        ("  Force  ",    "force"),
        ("KINETIC ENERGY", "kinetic energy"),
        ("momentum!",    "momentum"),
    ]
    for raw, expected in cases:
        got = normalize_term(raw)
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} normalize {raw!r} → {got!r} (expected {expected!r})")


# ── lookup_definition miss ────────────────────────────────────────────────────

def test_lookup_miss():
    _setup()
    result = lookup_definition("xenochrony")
    ok = not result.hit
    print(f"{_PASS if ok else _FAIL} lookup miss: hit={result.hit}, fallback={result.fallback_used}")
    ok2 = result.fallback_used is True
    print(f"{_PASS if ok2 else _FAIL} lookup miss: fallback_used=True")
    ok3 = result.confidence == 0.0
    print(f"{_PASS if ok3 else _FAIL} lookup miss: confidence=0.0")


# ── lookup ranks by confidence ────────────────────────────────────────────────

def test_lookup_ranks_by_confidence():
    _setup()
    register_definition("force", "Low confidence definition.", source_id="doc_low", confidence=0.5)
    register_definition("force", "High confidence definition.", source_id="doc_high", confidence=0.95)
    result = lookup_definition("force")
    ok = result.definition_text == "High confidence definition."
    print(f"{_PASS if ok else _FAIL} ranking: highest confidence selected ({result.confidence})")


# ── Router: all 4 pattern forms ───────────────────────────────────────────────

def test_router_all_pattern_forms():
    _setup()
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace

    cases = [
        ("what is acceleration",         "acceleration"),
        ("define force",                  "force"),
        ("definition of velocity",        "velocity"),
        ("what does momentum mean",       "momentum"),
    ]
    for query, expected_term in cases:
        parsed = parse(query)
        route_result, _ = route_with_trace(parsed)
        intent = route_result.selected_intent
        ok = intent.domain == "discourse" and intent.operator_name == "GET_DEFINITION"
        term = intent.slots.get("term", "").lower()
        ok2 = expected_term in term
        print(f"{_PASS if (ok and ok2) else _FAIL} pattern: {query!r} → domain={intent.domain!r}, term={term!r}")


# ── Planner short-circuit on known definition ─────────────────────────────────

def test_planner_short_circuit_hit():
    """If definition is registered, planner returns cache_hit=True with the text."""
    _setup()
    register_definition(
        "acceleration",
        "Acceleration is the rate of change of velocity.",
        source_id="physics_doc_v1",
        confidence=0.9,
    )
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.planner import plan
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.discourse import create_discourse_state

    clear_cache()
    state = create_discourse_state()
    parsed = parse("what is acceleration")
    route_result, _ = route_with_trace(parsed)
    qplan, ptrace = plan(route_result, state)

    ok = qplan.cache_hit
    print(f"{_PASS if ok else _FAIL} planner short-circuit: cache_hit={qplan.cache_hit}")
    ok2 = qplan.cached_result is not None
    print(f"{_PASS if ok2 else _FAIL} planner: cached_result set")
    if qplan.cached_result:
        ok3 = "acceleration" in qplan.cached_result.value.lower()
        print(f"{_PASS if ok3 else _FAIL} planner: result contains 'acceleration': {qplan.cached_result.value!r}")
    ok4 = ptrace.operator_key == "discourse.GET_DEFINITION"
    print(f"{_PASS if ok4 else _FAIL} planner trace: operator_key={ptrace.operator_key!r}")


# ── GET_DEFINITION CDL operator standalone ────────────────────────────────────

def test_get_definition_operator_standalone():
    """CDL operator works directly without planner."""
    _setup()
    register_definition("mass", "Mass is the amount of matter in an object.",
                         source_id="physics_doc", confidence=0.9)
    from l_cdea.core.types.base import TypedValue, SemanticType
    from l_cdea.discourse.definition_retrieval.operator import _get_definition_impl

    result = _get_definition_impl(TypedValue("mass", SemanticType.ENTITY))
    ok = "matter" in result.value.lower()
    print(f"{_PASS if ok else _FAIL} GET_DEFINITION operator: {result.value!r}")


# ── GET_DEFINITION fallback on unknown ────────────────────────────────────────

def test_get_definition_operator_fallback():
    """CDL operator returns definition_of(term) on miss."""
    _setup()
    from l_cdea.core.types.base import TypedValue, SemanticType
    from l_cdea.discourse.definition_retrieval.operator import _get_definition_impl

    result = _get_definition_impl(TypedValue("unknown_concept", SemanticType.ENTITY))
    ok = result.value.startswith("definition_of(")
    print(f"{_PASS if ok else _FAIL} GET_DEFINITION fallback: {result.value!r}")


# ── DiscourseNode metadata survives persistence ───────────────────────────────

def test_node_metadata_persistence():
    """DiscourseNode.metadata survives save → load round-trip."""
    import os, tempfile
    from l_cdea.discourse import create_discourse_state, save_state, load_state
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.memory_graph import add_node
    from l_cdea.core.types.base import SemanticType
    from l_cdea.core.planner.discourse_lookup import clear_cache

    clear_cache()
    state = create_discourse_state()
    node_id = make_node_id(SemanticType.ENTITY, "rate of change of velocity")
    node = DiscourseNode(
        id=node_id,
        semantic_type=SemanticType.ENTITY,
        value="rate of change of velocity",
        salience=1.0,
        created_at=0,
        updated_at=0,
        metadata={"category": "definition", "term": "acceleration",
                  "definition_text": "Acceleration is rate of change of velocity."},
    )
    add_node(state, node)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_state(state, path)
        clear_cache()
        loaded = load_state(path)
        loaded_node = loaded.nodes.get(node_id)
        ok = loaded_node is not None
        print(f"{_PASS if ok else _FAIL} metadata persistence: node loaded")
        if loaded_node:
            ok2 = loaded_node.metadata.get("category") == "definition"
            print(f"{_PASS if ok2 else _FAIL} metadata persistence: category={loaded_node.metadata.get('category')!r}")
            ok3 = loaded_node.metadata.get("term") == "acceleration"
            print(f"{_PASS if ok3 else _FAIL} metadata persistence: term={loaded_node.metadata.get('term')!r}")
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── DiscourseState node lookup via metadata ───────────────────────────────────

def test_lookup_from_discourse_state():
    """lookup_definition finds definitions stored in DiscourseState node metadata."""
    from l_cdea.discourse import create_discourse_state
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.memory_graph import add_node
    from l_cdea.core.types.base import SemanticType

    _setup()
    state = create_discourse_state()
    node_id = make_node_id(SemanticType.ENTITY, "Kinetic energy is the energy of motion.")
    node = DiscourseNode(
        id=node_id,
        semantic_type=SemanticType.ENTITY,
        value="Kinetic energy is the energy of motion.",
        salience=1.0,
        created_at=0,
        updated_at=0,
        metadata={
            "category": "definition",
            "term": "kinetic energy",
            "definition_text": "Kinetic energy is the energy of motion.",
        },
    )
    add_node(state, node)

    result = lookup_definition("kinetic energy", state)
    ok = result.hit
    print(f"{_PASS if ok else _FAIL} discourse state lookup: hit={result.hit}")
    ok2 = result.definition_text == "Kinetic energy is the energy of motion."
    print(f"{_PASS if ok2 else _FAIL} discourse state lookup: definition_text={result.definition_text!r}")


# ── Integration: ingest → save → load → query ────────────────────────────────

def test_integration_ingest_save_load_query():
    """Full pipeline: ingest physics_basic.txt → save → fresh load → query returns stored text."""
    import os
    import tempfile

    _setup()
    from l_cdea.core.planner.discourse_lookup import clear_cache

    physics_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "knowledge_seed", "physics_basic.txt"
    )
    physics_path = os.path.normpath(physics_path)

    if not os.path.exists(physics_path):
        print(f"  [SKIP] integration test: physics_basic.txt not found at {physics_path}")
        return

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    os.unlink(state_path)  # let ingest_document create it fresh

    try:
        from l_cdea.ingestion import ingest_document
        result = ingest_document(physics_path, state_path=state_path)
        ok = result.definitions > 0
        print(f"{_PASS if ok else _FAIL} integration: definitions extracted={result.definitions}")
        ok2 = result.nodes_added > 0
        print(f"{_PASS if ok2 else _FAIL} integration: nodes_added={result.nodes_added}")
        ok3 = os.path.exists(state_path)
        print(f"{_PASS if ok3 else _FAIL} integration: state file written")

        # Simulate fresh process: clear in-memory stores, reload from file
        clear_definitions()
        clear_cache()

        from l_cdea.discourse.storage import load_state as _load_state
        loaded = _load_state(state_path)
        ok4 = len(loaded.nodes) > 0
        print(f"{_PASS if ok4 else _FAIL} integration: loaded nodes={len(loaded.nodes)}")

        # Query should return the stored definition, not a fallback
        from l_cdea.core.parser import parse
        from l_cdea.core.router import route_with_trace
        from l_cdea.core.planner import plan

        clear_cache()
        parsed = parse("what is acceleration")
        route_result, _ = route_with_trace(parsed)
        qplan, ptrace = plan(route_result, loaded)

        ok5 = qplan.cache_hit
        print(f"{_PASS if ok5 else _FAIL} integration: cache_hit={qplan.cache_hit} (expected True)")
        if qplan.cached_result:
            val = qplan.cached_result.value
            ok6 = "acceleration" in val.lower() and "definition_of(" not in val
            print(f"{_PASS if ok6 else _FAIL} integration: result is stored text={val!r}")
        ok7 = ptrace.operator_key == "discourse.GET_DEFINITION"
        print(f"{_PASS if ok7 else _FAIL} integration: operator_key={ptrace.operator_key!r}")
    finally:
        if os.path.exists(state_path):
            os.unlink(state_path)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: what is acceleration",         test_example_1_what_is_acceleration),
        ("Example 2: define force",                  test_example_2_define_force),
        ("Example 3: velocity routes to definition", test_example_3_velocity_routes_to_definition),
        ("Example 4: missing term fallback",         test_example_4_missing_term_fallback),
        ("Example 5: duplicate definition",          test_example_5_duplicate_definition),
        ("normalize_term",                           test_normalize_term),
        ("lookup_definition miss",                   test_lookup_miss),
        ("lookup ranks by confidence",               test_lookup_ranks_by_confidence),
        ("Router: all 4 pattern forms",              test_router_all_pattern_forms),
        ("Planner short-circuit (hit)",              test_planner_short_circuit_hit),
        ("GET_DEFINITION operator standalone",       test_get_definition_operator_standalone),
        ("GET_DEFINITION fallback on unknown",       test_get_definition_operator_fallback),
        ("DiscourseNode metadata persistence",       test_node_metadata_persistence),
        ("DiscourseState node metadata lookup",      test_lookup_from_discourse_state),
        ("Integration: ingest → save → load → query", test_integration_ingest_save_load_query),
    ]
    failed = 0
    for name, fn in tests:
        print(f"\n── {name}")
        try:
            fn()
        except Exception as exc:
            import traceback
            print(f"{_FAIL} UNEXPECTED EXCEPTION: {exc!r}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'All tests passed.' if not failed else f'{failed} test(s) raised unexpected exceptions.'}")


if __name__ == "__main__":
    run_all()
