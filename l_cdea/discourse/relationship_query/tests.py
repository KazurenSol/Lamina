"""
Tests for l_cdea.discourse.relationship_query

Covers all four spec validation examples plus unit tests for
normalization, lookup, routing, planner short-circuit, and fallback.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))


# ── normalization ─────────────────────────────────────────────────────────────

def test_normalize_term():
    from l_cdea.discourse.relationship_query.normalization import normalize_term
    assert normalize_term("Force") == "force"
    assert normalize_term("  Acceleration  ") == "acceleration"
    assert normalize_term("mass.") == "mass"
    print("  [PASS] normalize_term")


def test_normalize_relation_type():
    from l_cdea.discourse.relationship_query.normalization import normalize_relation_type
    assert normalize_relation_type("depend on") == "depends_on"
    assert normalize_relation_type("depends on") == "depends_on"
    assert normalize_relation_type("related to") == "related_to"
    assert normalize_relation_type("causes") == "causes"
    assert normalize_relation_type("part of") == "part_of"
    print("  [PASS] normalize_relation_type")


# ── lookup ────────────────────────────────────────────────────────────────────

def _build_state_with_edges():
    """Return a DiscourseState with force→mass, force→acceleration edges."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.core.types.base import SemanticType

    state = create_empty()
    prov = Provenance(
        source_id="test", source_type="document",
        extraction_method="relationship_extractor", confidence=0.75,
        trace_id=make_trace_id("test", "relationship_extractor", 0),
        timestamp_index=0,
    )

    for term in ("force", "mass", "acceleration", "velocity"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))

    def nid(t): return make_node_id(SemanticType.ENTITY, t)

    add_edge(state, DiscourseEdge(
        source_id=nid("force"), target_id=nid("mass"),
        relation_type="depends_on", salience=0.75, provenance=(prov,)
    ))
    add_edge(state, DiscourseEdge(
        source_id=nid("force"), target_id=nid("acceleration"),
        relation_type="depends_on", salience=0.75, provenance=(prov,)
    ))
    add_edge(state, DiscourseEdge(
        source_id=nid("acceleration"), target_id=nid("velocity"),
        relation_type="depends_on", salience=0.75, provenance=(prov,)
    ))
    return state


def test_lookup_hit():
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    result, trace = lookup_relationships("force", "depends_on", state)
    assert result.hit
    assert set(result.values) == {"mass", "acceleration"}
    assert trace.hit
    assert not trace.fallback_used
    print(f"  [PASS] lookup_hit: values={sorted(result.values)}")


def test_lookup_miss_unknown_term():
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    result, trace = lookup_relationships("entropy", "depends_on", state)
    assert not result.hit
    assert trace.fallback_used
    print("  [PASS] lookup_miss_unknown_term")


def test_lookup_miss_no_edges():
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    result, trace = lookup_relationships("mass", "depends_on", state)
    assert not result.hit   # mass has no outgoing depends_on edges
    print("  [PASS] lookup_miss_no_edges")


def test_lookup_sorted_deterministic():
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    result1, _ = lookup_relationships("force", "depends_on", state)
    result2, _ = lookup_relationships("force", "depends_on", state)
    assert result1.values == result2.values
    print("  [PASS] lookup_sorted_deterministic")


# ── router ────────────────────────────────────────────────────────────────────

def test_router_depends_on():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what does force depend on")
    result, trace = route_with_trace(parsed)
    intent = result.selected_intent
    assert intent.domain == "discourse"
    assert intent.operator_name == "GET_RELATIONSHIPS"
    assert intent.slots.get("term") == "force"
    assert intent.slots.get("relation_type") == "depends_on"
    print(f"  [PASS] router_depends_on: slots={intent.slots}")


def test_router_what_is_still_definition():
    """Example 4: 'what is force' must still route to GET_DEFINITION."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what is force")
    result, _ = route_with_trace(parsed)
    assert result.selected_intent.operator_name == "GET_DEFINITION"
    print("  [PASS] router_what_is_still_definition")


# ── planner short-circuit ─────────────────────────────────────────────────────

def test_planner_hit():
    """Example 1: ingested force sentence → planner returns relationship hit."""
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult

    state = _build_state_with_edges()
    intent = IntentFrame(
        domain="discourse", operator_name="GET_RELATIONSHIPS",
        slots={"term": "force", "relation_type": "depends_on"},
        confidence=1.19,
        source_pattern_id="discourse.rel.depends_on",
        fallback=False,
        arg_order=("term", "relation_type"),
    )
    route_result = RouteResult(
        intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False
    )
    qplan, ptrace = plan(route_result, state)
    assert qplan.cache_hit
    assert qplan.cache_trace.get("strategy") == "relationship_query"
    assert qplan.cache_trace.get("hit") is True
    values = qplan.cache_trace.get("returned_values", [])
    assert "mass" in values
    assert "acceleration" in values
    print(f"  [PASS] planner_hit: returned_values={sorted(values)}")


def test_planner_fallback():
    """Example 3: unknown term → cache_hit=False, fallback=True."""
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    from l_cdea.discourse.state import create_empty

    state = create_empty()
    intent = IntentFrame(
        domain="discourse", operator_name="GET_RELATIONSHIPS",
        slots={"term": "entropy", "relation_type": "depends_on"},
        confidence=1.19,
        source_pattern_id="discourse.rel.depends_on",
        fallback=False,
        arg_order=("term", "relation_type"),
    )
    route_result = RouteResult(
        intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False
    )
    qplan, _ = plan(route_result, state)
    assert not qplan.cache_hit
    assert qplan.cache_trace.get("strategy") == "relationship_query"
    assert qplan.cache_trace.get("fallback") is True
    assert "entropy" in str(qplan.cached_result.value)
    print(f"  [PASS] planner_fallback: value={qplan.cached_result.value!r}")


# ── end-to-end integration ────────────────────────────────────────────────────

def test_e2e_example1_force():
    """End-to-end: ingest → store → query 'what does force depend on'."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import RouteResult

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Force is mass times acceleration.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        parsed = parse("what does force depend on")
        route_result, _ = route_with_trace(parsed)
        assert route_result.selected_intent.operator_name == "GET_RELATIONSHIPS"

        qplan, _ = plan(route_result, state)
        assert qplan.cache_hit
        values = qplan.cache_trace.get("returned_values", [])
        assert "mass" in values
        assert "acceleration" in values
        print(f"  [PASS] e2e_example1_force: {sorted(values)}")


def test_e2e_example2_acceleration():
    """End-to-end: ingest → query 'what does acceleration depend on'."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Acceleration is the rate of change of velocity.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        parsed = parse("what does acceleration depend on")
        route_result, _ = route_with_trace(parsed)
        qplan, _ = plan(route_result, state)

        assert qplan.cache_hit
        values = qplan.cache_trace.get("returned_values", [])
        assert "velocity" in values
        print(f"  [PASS] e2e_example2_acceleration: {values}")


def test_e2e_example3_entropy_fallback():
    """End-to-end: unknown term → fallback output."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan

    state = create_empty()
    parsed = parse("what does entropy depend on")
    route_result, _ = route_with_trace(parsed)
    assert route_result.selected_intent.operator_name == "GET_RELATIONSHIPS"

    qplan, _ = plan(route_result, state)
    assert not qplan.cache_hit
    assert "entropy" in str(qplan.cached_result.value)
    print(f"  [PASS] e2e_example3_entropy_fallback: {qplan.cached_result.value!r}")


# ── relationship provenance display ───────────────────────────────────────────

def test_lookup_results_carry_provenance():
    """Each RelationshipResult in results must include its edge provenance."""
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    result, trace = lookup_relationships("force", "depends_on", state)
    assert result.hit
    assert len(result.results) == 2
    for rel_res in result.results:
        assert rel_res.provenance, f"no provenance on {rel_res.target_value}"
        assert rel_res.source_term == "force"
        assert rel_res.relation_type == "depends_on"
    print("  [PASS] lookup_results_carry_provenance")


def test_extract_relationship_provenance():
    """extract_relationship_provenance returns DisplayedProvenance from RelationshipResult."""
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    from l_cdea.trace.provenance_display import extract_relationship_provenance
    state = _build_state_with_edges()
    result, _ = lookup_relationships("acceleration", "depends_on", state)
    assert result.hit
    rel_res = result.results[0]   # acceleration → velocity
    entries = extract_relationship_provenance(rel_res)
    assert len(entries) >= 1
    assert entries[0].confidence == 0.75
    assert entries[0].extraction_method == "relationship_extractor"
    print(f"  [PASS] extract_relationship_provenance: conf={entries[0].confidence}")


def test_extract_relationship_provenance_empty():
    """Empty provenance degrades gracefully."""
    from l_cdea.discourse.relationship_query.lookup import RelationshipResult
    from l_cdea.trace.provenance_display import extract_relationship_provenance
    rel_res = RelationshipResult(
        target_value="velocity", relation_type="depends_on",
        source_term="acceleration", edge_id=None, provenance=()
    )
    entries = extract_relationship_provenance(rel_res)
    assert entries == ()
    print("  [PASS] extract_relationship_provenance_empty")


def test_trace_matched_edges_are_dicts():
    """RelationshipQueryTrace.matched_edges must be list of dicts with per-edge detail."""
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    state = _build_state_with_edges()
    _, trace = lookup_relationships("force", "depends_on", state)
    assert trace.hit
    assert isinstance(trace.matched_edges, list)
    assert len(trace.matched_edges) == 2
    for edge_dict in trace.matched_edges:
        assert "target_value" in edge_dict
        assert "provenance_entries" in edge_dict
        assert "provenance_count" in edge_dict
        assert edge_dict["provenance_count"] >= 1
    print("  [PASS] trace_matched_edges_are_dicts")


def test_planner_results_in_cache_trace():
    """Planner hit must include 'results' in cache_trace for provenance display."""
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    state = _build_state_with_edges()
    intent = IntentFrame(
        domain="discourse", operator_name="GET_RELATIONSHIPS",
        slots={"term": "force", "relation_type": "depends_on"},
        confidence=1.19, source_pattern_id="discourse.rel.depends_on",
        fallback=False, arg_order=("term", "relation_type"),
    )
    route_result = RouteResult(
        intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False
    )
    qplan, _ = plan(route_result, state)
    assert qplan.cache_hit
    results = qplan.cache_trace.get("results", ())
    assert len(results) == 2
    for r in results:
        assert len(r.provenance) >= 1
    print(f"  [PASS] planner_results_in_cache_trace: {len(results)} results with provenance")


def test_e2e_provenance_display_force():
    """Example 1: end-to-end ingest → query shows per-edge provenance."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan
    from l_cdea.trace.provenance_display import extract_relationship_provenance, format_provenance_lines
    from l_cdea.trace.provenance_display.config import DEFAULT_CONFIG

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Force is mass times acceleration.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        parsed = parse("what does force depend on")
        route_result, _ = route_with_trace(parsed)
        qplan, _ = plan(route_result, state)

        results = qplan.cache_trace.get("results", ())
        assert len(results) == 2
        for rel_res in results:
            entries = extract_relationship_provenance(rel_res)
            assert len(entries) >= 1, f"no provenance for {rel_res.target_value}"
            lines = format_provenance_lines(entries, DEFAULT_CONFIG)
            assert lines, f"no formatted lines for {rel_res.target_value}"
            assert "source:" in lines[0], f"expected source label: {lines[0]}"
            assert "conf:" in lines[0], f"expected confidence: {lines[0]}"
            print(f"    {rel_res.target_value}: {lines[0].strip()}")
        print("  [PASS] e2e_provenance_display_force")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── normalization", [test_normalize_term, test_normalize_relation_type]),
        ("── lookup", [test_lookup_hit, test_lookup_miss_unknown_term,
                       test_lookup_miss_no_edges, test_lookup_sorted_deterministic]),
        ("── router", [test_router_depends_on, test_router_what_is_still_definition]),
        ("── planner", [test_planner_hit, test_planner_fallback]),
        ("── end-to-end", [test_e2e_example1_force, test_e2e_example2_acceleration,
                           test_e2e_example3_entropy_fallback]),
        ("── relationship provenance", [
            test_lookup_results_carry_provenance,
            test_extract_relationship_provenance,
            test_extract_relationship_provenance_empty,
            test_trace_matched_edges_are_dicts,
            test_planner_results_in_cache_trace,
            test_e2e_provenance_display_force,
        ]),
    ]

    failures = 0
    for title, tests in sections:
        print(f"\n{title}")
        for t in tests:
            try:
                t()
            except Exception as exc:
                print(f"  [FAIL] {t.__name__}: {exc}")
                import traceback; traceback.print_exc()
                failures += 1

    print()
    if failures:
        print(f"{failures} test(s) failed.")
        sys.exit(1)
    else:
        print("All tests passed.")
