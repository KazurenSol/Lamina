"""
Tests for l_cdea.discourse.multi_hop_reasoning

Covers all five spec validation examples plus unit tests for
traversal, cycle detection, max_depth, router, and planner.
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

    add_edge(state, DiscourseEdge(nid("force"), nid("mass"),       "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("force"), nid("acceleration"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("acceleration"), nid("velocity"), "depends_on", 0.75, (prov,)))
    return state


def _build_cycle_state():
    """A→B, B→A (cycle)."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.core.types.base import SemanticType

    state = create_empty()
    prov = _make_provenance("cycle", 0)
    for term in ("a", "b"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))
    def nid(t): return make_node_id(SemanticType.ENTITY, t)
    add_edge(state, DiscourseEdge(nid("a"), nid("b"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("b"), nid("a"), "depends_on", 0.75, (prov,)))
    return state


def _build_chain_state():
    """A→B→C→D (linear chain)."""
    from l_cdea.discourse.state import create_empty
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.edge import DiscourseEdge
    from l_cdea.discourse.memory_graph import add_node, add_edge
    from l_cdea.core.types.base import SemanticType

    state = create_empty()
    prov = _make_provenance("chain", 0)
    for term in ("a", "b", "c", "d"):
        nid = make_node_id(SemanticType.ENTITY, term)
        add_node(state, DiscourseNode(
            id=nid, semantic_type=SemanticType.ENTITY, value=term,
            salience=0.5, created_at=0, updated_at=0, provenance=(prov,),
        ))
    def nid(t): return make_node_id(SemanticType.ENTITY, t)
    add_edge(state, DiscourseEdge(nid("a"), nid("b"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("b"), nid("c"), "depends_on", 0.75, (prov,)))
    add_edge(state, DiscourseEdge(nid("c"), nid("d"), "depends_on", 0.75, (prov,)))
    return state


# ── traversal ─────────────────────────────────────────────────────────────────

def test_example1_force_closure():
    """Example 1: force → acceleration, mass, velocity (multi-hop)."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_physics_state()
    result, trace = compute_closure("force", "depends_on", state, max_depth=3)
    assert not result.fallback_used
    targets = {p.target for p in result.paths}
    assert "mass" in targets
    assert "acceleration" in targets
    assert "velocity" in targets
    assert len(result.paths) == 3
    print(f"  [PASS] example1_force_closure: targets={sorted(targets)}")


def test_example1_path_ordering():
    """Paths must be sorted: depth ASC, target ASC."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_physics_state()
    result, _ = compute_closure("force", "depends_on", state)
    depths = [p.depth for p in result.paths]
    assert depths == sorted(depths), f"not sorted by depth: {depths}"
    # depth-1 entries: acceleration and mass (alphabetical)
    d1 = [p.target for p in result.paths if p.depth == 1]
    assert d1 == sorted(d1), f"depth-1 not sorted: {d1}"
    print(f"  [PASS] example1_path_ordering: {[(p.depth, p.target) for p in result.paths]}")


def test_example2_acceleration_closure():
    """Example 2: acceleration → velocity only."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_physics_state()
    result, trace = compute_closure("acceleration", "depends_on", state)
    assert not result.fallback_used
    assert len(result.paths) == 1
    assert result.paths[0].target == "velocity"
    assert result.paths[0].depth == 1
    print("  [PASS] example2_acceleration_closure")


def test_example3_cycle_detection():
    """Example 3: A→B→A — returns B, cycle_detected=True, no infinite loop."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_cycle_state()
    result, trace = compute_closure("a", "depends_on", state)
    assert not result.fallback_used
    targets = {p.target for p in result.paths}
    assert "b" in targets
    assert "a" not in targets   # cycle back to source not added as path
    assert trace.cycle_detected
    print(f"  [PASS] example3_cycle_detection: targets={sorted(targets)}, cycle_detected={trace.cycle_detected}")


def test_example4_max_depth():
    """Example 4: A→B→C→D with max_depth=2 — returns B and C, not D."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_chain_state()
    result, trace = compute_closure("a", "depends_on", state, max_depth=2)
    targets = {p.target for p in result.paths}
    assert "b" in targets
    assert "c" in targets
    assert "d" not in targets
    print(f"  [PASS] example4_max_depth: targets={sorted(targets)} (d excluded)")


def test_example5_fallback():
    """Example 5: unknown term → fallback_used=True."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    from l_cdea.discourse.state import create_empty
    state = create_empty()
    result, trace = compute_closure("entropy", "depends_on", state)
    assert result.fallback_used
    assert len(result.paths) == 0
    assert trace.fallback_used
    print("  [PASS] example5_fallback")


def test_provenance_aggregated_along_path():
    """force→acceleration→velocity path must carry provenance from both edges."""
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
    state = _build_physics_state()
    result, _ = compute_closure("force", "depends_on", state)
    velocity_paths = [p for p in result.paths if p.target == "velocity"]
    assert len(velocity_paths) == 1
    vp = velocity_paths[0]
    assert vp.depth == 2
    assert vp.path == ("force", "acceleration", "velocity")
    assert len(vp.provenance) == 2   # one from each edge
    print(f"  [PASS] provenance_aggregated: depth={vp.depth}, prov_count={len(vp.provenance)}")


# ── router ────────────────────────────────────────────────────────────────────

def test_router_ultimately():
    """'show dependency chain for X' still routes to GET_RELATIONSHIP_CLOSURE."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("show dependency chain for force")
    result, _ = route_with_trace(parsed)
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    assert intent.slots.get("relation_type") == "depends_on"
    print(f"  [PASS] router_closure_chain: slots={intent.slots}")


def test_router_all_dependencies():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what are all dependencies of acceleration")
    result, _ = route_with_trace(parsed)
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "acceleration"
    print(f"  [PASS] router_all_dependencies: term={intent.slots.get('term')}")


def test_router_one_hop_still_works():
    """'what does X depend on' must still route to GET_RELATIONSHIPS (not closure)."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    parsed = parse("what does force depend on")
    result, _ = route_with_trace(parsed)
    assert result.selected_intent.operator_name == "GET_RELATIONSHIPS"
    print("  [PASS] router_one_hop_still_works")


# ── planner ───────────────────────────────────────────────────────────────────

def test_planner_closure_hit():
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    state = _build_physics_state()
    intent = IntentFrame(
        domain="discourse", operator_name="GET_RELATIONSHIP_CLOSURE",
        slots={"term": "force", "relation_type": "depends_on", "max_depth": "3"},
        confidence=1.195, source_pattern_id="discourse.mh.ultimately_depends_on",
        fallback=False, arg_order=("term", "relation_type", "max_depth"),
    )
    route_result = RouteResult(intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False)
    qplan, _ = plan(route_result, state)
    assert qplan.cache_hit
    assert qplan.cache_trace.get("strategy") == "multi_hop_closure"
    closure_result = qplan.cache_trace.get("closure_result")
    assert closure_result is not None
    targets = {p.target for p in closure_result.paths}
    assert "velocity" in targets
    print(f"  [PASS] planner_closure_hit: targets={sorted(targets)}")


def test_planner_closure_fallback():
    from l_cdea.core.planner import plan
    from l_cdea.core.router.intent import IntentFrame, RouteResult
    from l_cdea.discourse.state import create_empty
    state = create_empty()
    intent = IntentFrame(
        domain="discourse", operator_name="GET_RELATIONSHIP_CLOSURE",
        slots={"term": "entropy", "relation_type": "depends_on", "max_depth": "3"},
        confidence=1.195, source_pattern_id="discourse.mh.ultimately_depends_on",
        fallback=False, arg_order=("term", "relation_type", "max_depth"),
    )
    route_result = RouteResult(intents=(intent,), selected_intent=intent, ambiguous=False, fallback_used=False)
    qplan, _ = plan(route_result, state)
    assert not qplan.cache_hit
    assert qplan.cache_trace.get("fallback") is True
    assert "entropy" in str(qplan.cached_result.value)
    print(f"  [PASS] planner_closure_fallback: {qplan.cached_result.value!r}")


# ── end-to-end integration ────────────────────────────────────────────────────

def test_e2e_force_ultimately():
    """End-to-end: ingest two sentences, query for multi-hop closure."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    from l_cdea.core.planner import plan

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Force is mass times acceleration.\n")
            f.write("Acceleration is the rate of change of velocity.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        parsed = parse("show dependency chain for force")
        route_result, _ = route_with_trace(parsed)
        assert route_result.selected_intent.operator_name == "GET_RELATIONSHIP_CLOSURE"

        qplan, _ = plan(route_result, state)
        assert qplan.cache_hit
        closure = qplan.cache_trace.get("closure_result")
        targets = {p.target for p in closure.paths}
        assert "mass" in targets
        assert "acceleration" in targets
        assert "velocity" in targets
        print(f"  [PASS] e2e_force_ultimately: {sorted(targets)}")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── traversal", [
            test_example1_force_closure,
            test_example1_path_ordering,
            test_example2_acceleration_closure,
            test_example3_cycle_detection,
            test_example4_max_depth,
            test_example5_fallback,
            test_provenance_aggregated_along_path,
        ]),
        ("── router", [
            test_router_ultimately,
            test_router_all_dependencies,
            test_router_one_hop_still_works,
        ]),
        ("── planner", [
            test_planner_closure_hit,
            test_planner_closure_fallback,
        ]),
        ("── end-to-end", [
            test_e2e_force_ultimately,
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
