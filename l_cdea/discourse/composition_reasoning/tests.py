"""
Tests for l_cdea.discourse.composition_reasoning

Covers all four spec validation examples plus unit tests for
rules, composer, router, planner, and end-to-end.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_provenance(source_id: str = "test", idx: int = 0):
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    return Provenance(
        source_id=source_id, source_type="document",
        extraction_method="relationship_extractor", confidence=0.75,
        trace_id=make_trace_id(source_id, "relationship_extractor", idx),
        timestamp_index=idx,
    )


def _build_physics_state():
    """force→mass, force→acceleration, acceleration→velocity."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.core.types.base import SemanticType

    state = create_empty()
    prov = _make_provenance("physics", 0)

    for term in ("force", "mass", "acceleration", "velocity"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))

    def nid(t): return make_node_id(SemanticType.ENTITY, t)

    add_edge(state, DiscourseEdge(nid("force"), nid("mass"),         "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("force"), nid("acceleration"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("acceleration"), nid("velocity"), "depends_on", 0.75, (_make_provenance("physics", 1),)))
    return state


def _build_diamond_state():
    """A→B→D, A→C→D (diamond — D reachable via two indirect paths)."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.core.types.base import SemanticType

    state = create_empty()
    prov = _make_provenance("diamond", 0)
    for term in ("a", "b", "c", "d"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))
    def nid(t): return make_node_id(SemanticType.ENTITY, t)
    add_edge(state, DiscourseEdge(nid("a"), nid("b"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("a"), nid("c"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("b"), nid("d"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("c"), nid("d"), "depends_on", 0.75, (prov,)))
    return state


# ── composer / rules ──────────────────────────────────────────────────────────

def test_example1_force_direct_indirect():
    """Example 1: force → direct: mass, acceleration; indirect: velocity."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    state = _build_physics_state()
    result, trace = compose("force", "depends_on", state, max_depth=3)
    assert not result.fallback_used
    direct_targets = {cr.target for cr in result.direct}
    indirect_targets = {cr.target for cr in result.indirect}
    assert direct_targets == {"mass", "acceleration"}, f"direct={direct_targets}"
    assert indirect_targets == {"velocity"}, f"indirect={indirect_targets}"
    print(f"  [PASS] example1_force: direct={sorted(direct_targets)}, indirect={sorted(indirect_targets)}")


def test_example1_direct_sorted():
    """Direct entries are sorted alphabetically."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    state = _build_physics_state()
    result, _ = compose("force", "depends_on", state)
    direct_names = [cr.target for cr in result.direct]
    assert direct_names == sorted(direct_names), f"not sorted: {direct_names}"
    print(f"  [PASS] example1_direct_sorted: {direct_names}")


def test_example2_acceleration_no_indirect():
    """Example 2: acceleration → direct: velocity; indirect: none."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    state = _build_physics_state()
    result, trace = compose("acceleration", "depends_on", state)
    assert not result.fallback_used
    assert len(result.direct) == 1
    assert result.direct[0].target == "velocity"
    assert len(result.indirect) == 0
    print(f"  [PASS] example2_acceleration: direct=['velocity'], indirect=[]")


def test_example3_diamond_deduplication():
    """Example 3: A→B→D, A→C→D — D appears once in indirect with both paths."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    state = _build_diamond_state()
    result, trace = compose("a", "depends_on", state)
    assert not result.fallback_used
    direct_targets = {cr.target for cr in result.direct}
    indirect_targets = {cr.target for cr in result.indirect}
    assert direct_targets == {"b", "c"}, f"direct={direct_targets}"
    assert "d" in indirect_targets, f"d not in indirect={indirect_targets}"
    # d appears exactly once
    d_entries = [cr for cr in result.indirect if cr.target == "d"]
    assert len(d_entries) == 1
    # d has two paths
    assert len(d_entries[0].paths) == 2, f"expected 2 paths for d, got {len(d_entries[0].paths)}"
    print(f"  [PASS] example3_diamond: d has {len(d_entries[0].paths)} paths")


def test_example4_fallback():
    """Example 4: entropy → fallback_used=True, compose_of string."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    from l_cdea.discourse.state import create_empty
    state = create_empty()
    result, trace = compose("entropy", "depends_on", state)
    assert result.fallback_used
    assert len(result.direct) == 0
    assert len(result.indirect) == 0
    assert trace.fallback_used
    print(f"  [PASS] example4_fallback: fallback_used={result.fallback_used}")


def test_dominance_rule():
    """If target is reachable directly AND indirectly, it goes in direct only."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.core.types.base import SemanticType
    from l_cdea.discourse.composition_reasoning.composer import compose

    # A→B (direct), A→C→B (indirect) — B should appear in direct only
    state = create_empty()
    prov = _make_provenance("dom", 0)
    for term in ("a", "b", "c"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))
    def nid(t): return make_node_id(SemanticType.ENTITY, t)
    add_edge(state, DiscourseEdge(nid("a"), nid("b"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("a"), nid("c"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("c"), nid("b"), "depends_on", 0.75, (prov,)))

    result, _ = compose("a", "depends_on", state)
    direct_targets = {cr.target for cr in result.direct}
    indirect_targets = {cr.target for cr in result.indirect}
    assert "b" in direct_targets, f"b should be direct: {direct_targets}"
    assert "b" not in indirect_targets, f"b should NOT be indirect: {indirect_targets}"
    print(f"  [PASS] dominance_rule: b in direct={direct_targets}, not in indirect={indirect_targets}")


def test_provenance_aggregated():
    """force→acceleration→velocity path aggregates 2 provenance entries."""
    from l_cdea.discourse.composition_reasoning.composer import compose
    state = _build_physics_state()
    result, _ = compose("force", "depends_on", state)
    velocity_entries = [cr for cr in result.indirect if cr.target == "velocity"]
    assert len(velocity_entries) == 1
    vp = velocity_entries[0]
    assert len(vp.provenance) == 2, f"expected 2 prov entries, got {len(vp.provenance)}"
    print(f"  [PASS] provenance_aggregated: velocity has {len(vp.provenance)} provenance entries")


# ── router ────────────────────────────────────────────────────────────────────

def test_router_indirectly():
    """'what does X indirectly depend on' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what does force indirectly depend on")
    result, _ = route_with_trace(parsed)
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    assert intent.slots.get("relation_type") == "depends_on"
    print(f"  [PASS] router_indirectly: slots={intent.slots}")


def test_router_ultimately_routes_to_composition():
    """'what does X ultimately depend on' → COMPOSE_RELATIONSHIPS (priority 196 wins over 195)."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what does force ultimately depend on")
    result, _ = route_with_trace(parsed)
    assert result.selected_intent.operator_name == "COMPOSE_RELATIONSHIPS", \
        f"got {result.selected_intent.operator_name}"
    print(f"  [PASS] router_ultimately_to_composition")


def test_router_indirect_dependencies():
    """'what are indirect dependencies of X' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what are indirect dependencies of acceleration")
    result, _ = route_with_trace(parsed)
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "acceleration", f"term={intent.slots.get('term')}"
    print(f"  [PASS] router_indirect_dependencies: term={intent.slots.get('term')}")


def test_router_one_hop_unchanged():
    """'what does X depend on' still routes to GET_RELATIONSHIPS (not composition)."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what does force depend on")
    result, _ = route_with_trace(parsed)
    assert result.selected_intent.operator_name == "GET_RELATIONSHIPS", \
        f"got {result.selected_intent.operator_name}"
    print(f"  [PASS] router_one_hop_unchanged")


# ── planner ───────────────────────────────────────────────────────────────────

def test_planner_composition_hit():
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    state = _build_physics_state()
    intent = IntentFrame(
        domain="discourse", operator_name="COMPOSE_RELATIONSHIPS",
        slots={"term": "force", "relation_type": "depends_on", "max_depth": "3"},
        confidence=1.196, source_pattern_id="discourse.cr.indirectly_depends_on",
        fallback=False, arg_order=("term", "relation_type", "max_depth"),
    )
    route_result = RouteResult(intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False)
    qplan, _ = plan(route_result, state)
    assert qplan.cache_hit
    assert qplan.cache_trace.get("strategy") == "composition_reasoning"
    comp_result = qplan.cache_trace.get("comp_result")
    assert comp_result is not None
    direct_targets = {cr.target for cr in comp_result.direct}
    indirect_targets = {cr.target for cr in comp_result.indirect}
    assert "velocity" in indirect_targets
    assert "mass" in direct_targets
    print(f"  [PASS] planner_composition_hit: direct={sorted(direct_targets)}, indirect={sorted(indirect_targets)}")


def test_planner_composition_fallback():
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    from l_cdea.discourse.state import create_empty
    state = create_empty()
    intent = IntentFrame(
        domain="discourse", operator_name="COMPOSE_RELATIONSHIPS",
        slots={"term": "entropy", "relation_type": "depends_on", "max_depth": "3"},
        confidence=1.196, source_pattern_id="discourse.cr.indirectly_depends_on",
        fallback=False, arg_order=("term", "relation_type", "max_depth"),
    )
    route_result = RouteResult(intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False)
    qplan, _ = plan(route_result, state)
    assert not qplan.cache_hit
    assert qplan.cache_trace.get("fallback") is True
    assert "entropy" in str(qplan.cached_result.value)
    print(f"  [PASS] planner_composition_fallback: {qplan.cached_result.value!r}")


# ── end-to-end ────────────────────────────────────────────────────────────────

def test_e2e_force_indirectly():
    """End-to-end: ingest two sentences, query for composition."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Force is mass times acceleration.\n")
            f.write("Acceleration is the rate of change of velocity.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        parsed = parse("what does force indirectly depend on")
        route_result, _ = route_with_trace(parsed)
        assert route_result.selected_intent.operator_name == "COMPOSE_RELATIONSHIPS"

        qplan, _ = plan(route_result, state)
        assert qplan.cache_hit
        comp = qplan.cache_trace.get("comp_result")
        direct_targets = {cr.target for cr in comp.direct}
        indirect_targets = {cr.target for cr in comp.indirect}
        assert "mass" in direct_targets
        assert "acceleration" in direct_targets
        assert "velocity" in indirect_targets
        print(f"  [PASS] e2e_force_indirectly: direct={sorted(direct_targets)}, indirect={sorted(indirect_targets)}")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── composer / rules", [
            test_example1_force_direct_indirect,
            test_example1_direct_sorted,
            test_example2_acceleration_no_indirect,
            test_example3_diamond_deduplication,
            test_example4_fallback,
            test_dominance_rule,
            test_provenance_aggregated,
        ]),
        ("── router", [
            test_router_indirectly,
            test_router_ultimately_routes_to_composition,
            test_router_indirect_dependencies,
            test_router_one_hop_unchanged,
        ]),
        ("── planner", [
            test_planner_composition_hit,
            test_planner_composition_fallback,
        ]),
        ("── end-to-end", [
            test_e2e_force_indirectly,
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
