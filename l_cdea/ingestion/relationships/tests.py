"""
Tests for l_cdea.ingestion.relationships

Covers all four spec validation examples plus edge cases:
  normalizer, patterns, extractor, edge_builder, integration.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))


def _make_provenance(source_id: str = "test", idx: int = 0):
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    return Provenance(
        source_id=source_id,
        source_type="document",
        extraction_method="relationship_extractor",
        confidence=0.75,
        trace_id=make_trace_id(source_id, "relationship_extractor", idx),
        timestamp_index=idx,
        source_path=None,
        chunk_id=None,
        location=None,
    )


# ── normalizer ────────────────────────────────────────────────────────────────

def test_normalize_basic():
    from l_cdea.ingestion.relationships.normalizer import normalize_term
    assert normalize_term("  Force  ") == "force"
    assert normalize_term("A car") == "car"
    assert normalize_term("an Object") == "object"
    assert normalize_term("the  Rate") == "rate"
    assert normalize_term("mass.") == "mass"
    print("  [PASS] normalize_basic")


def test_normalize_collapse_whitespace():
    from l_cdea.ingestion.relationships.normalizer import normalize_term
    assert normalize_term("rate  of   change") == "rate of change"
    print("  [PASS] normalize_collapse_whitespace")


# ── patterns ──────────────────────────────────────────────────────────────────

def test_pattern_times():
    from l_cdea.ingestion.relationships.patterns import ALL_PATTERNS
    text = "Force is mass times acceleration."
    for p in ALL_PATTERNS:
        result = p.match(text)
        if result:
            assert p.name == "is_times", f"wrong pattern: {p.name}"
            sources = {r[0].lower() for r in result}
            targets = {r[2].lower() for r in result}
            assert "force" in sources
            assert "mass" in targets
            assert "acceleration" in targets
            assert all(r[1] == "depends_on" for r in result)
            print("  [PASS] pattern_times")
            return
    assert False, "no pattern matched"


def test_pattern_rate_of_change():
    from l_cdea.ingestion.relationships.patterns import ALL_PATTERNS
    text = "Acceleration is the rate of change of velocity."
    for p in ALL_PATTERNS:
        result = p.match(text)
        if result:
            assert p.name == "rate_of_change", f"wrong pattern: {p.name}"
            assert result[0][0].lower() == "acceleration"
            assert result[0][2].lower() == "velocity"
            assert result[0][1] == "depends_on"
            print("  [PASS] pattern_rate_of_change")
            return
    assert False, "no pattern matched"


def test_pattern_is_a_article():
    from l_cdea.ingestion.relationships.patterns import ALL_PATTERNS
    text = "A car is a vehicle."
    for p in ALL_PATTERNS:
        result = p.match(text)
        if result:
            assert p.name == "is_a_article", f"wrong pattern: {p.name}"
            assert result[0][1] == "is_a"
            print("  [PASS] pattern_is_a_article")
            return
    assert False, "no pattern matched"


def test_no_match():
    from l_cdea.ingestion.relationships.patterns import ALL_PATTERNS
    text = "Velocity."
    for p in ALL_PATTERNS:
        result = p.match(text)
        if result is not None:
            assert False, f"unexpected match from {p.name}: {result}"
    print("  [PASS] no_match")


# ── extractor ─────────────────────────────────────────────────────────────────

def test_example1_force():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    prov = _make_provenance("physics")
    result = extract_relationships("Force is mass times acceleration.", prov)
    assert len(result.edges) == 2
    terms = {e.target_term for e in result.edges}
    assert "mass" in terms
    assert "acceleration" in terms
    assert all(e.source_term == "force" for e in result.edges)
    assert all(e.relation_type == "depends_on" for e in result.edges)
    print("  [PASS] example1_force")


def test_example2_acceleration():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    prov = _make_provenance("physics")
    result = extract_relationships("Acceleration is the rate of change of velocity.", prov)
    assert len(result.edges) == 1
    e = result.edges[0]
    assert e.source_term == "acceleration"
    assert e.target_term == "velocity"
    assert e.relation_type == "depends_on"
    print("  [PASS] example2_acceleration")


def test_example3_car():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    prov = _make_provenance("ontology")
    result = extract_relationships("A car is a vehicle.", prov)
    assert len(result.edges) == 1
    e = result.edges[0]
    assert e.source_term == "car"
    assert e.target_term == "vehicle"
    assert e.relation_type == "is_a"
    print("  [PASS] example3_car")


def test_example4_no_relationships():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    prov = _make_provenance("physics")
    result = extract_relationships("Velocity.", prov)
    assert len(result.edges) == 0
    print("  [PASS] example4_no_relationships")


def test_multi_sentence():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    prov = _make_provenance("doc")
    text = "Force is mass times acceleration. A car is a vehicle."
    result = extract_relationships(text, prov)
    assert len(result.edges) == 3   # 2 from force, 1 from car
    print("  [PASS] multi_sentence")


# ── edge_builder ──────────────────────────────────────────────────────────────

def test_edge_builder_creates_nodes_and_edges():
    from l_cdea.ingestion.relationships.extractor import extract_relationships, RelationshipEdge
    from l_cdea.ingestion.relationships.edge_builder import build_edges
    from l_cdea.discourse.state import create_empty
    prov = _make_provenance("physics", 0)
    result = extract_relationships("Force is mass times acceleration.", prov)
    state = create_empty()
    count = build_edges(list(result.edges), state)
    assert count == 2
    assert len(state.edges) == 2
    # Term nodes: force, mass, acceleration
    term_values = {n.value for n in state.nodes.values()}
    assert "force" in term_values
    assert "mass" in term_values
    assert "acceleration" in term_values
    print("  [PASS] edge_builder_creates_nodes_and_edges")


def test_edge_builder_deduplicates():
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    from l_cdea.ingestion.relationships.edge_builder import build_edges
    from l_cdea.discourse.state import create_empty
    prov1 = _make_provenance("src1", 0)
    prov2 = _make_provenance("src2", 1)
    result1 = extract_relationships("Force is mass times acceleration.", prov1)
    result2 = extract_relationships("Force is mass times acceleration.", prov2)
    state = create_empty()
    count1 = build_edges(list(result1.edges), state)
    count2 = build_edges(list(result2.edges), state)
    assert count1 == 2
    assert count2 == 0   # duplicates — merged, not added
    assert len(state.edges) == 2
    # Provenance should be merged: each edge has 2 provenance entries
    for edge in state.edges:
        assert len(edge.provenance) == 2, f"expected 2 provs, got {len(edge.provenance)}"
    print("  [PASS] edge_builder_deduplicates")


# ── integration with ingest_document ─────────────────────────────────────────

def test_ingest_document_extracts_relationships():
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("Force is mass times acceleration.\n")
            f.write("Acceleration is the rate of change of velocity.\n")

        result = ingest_document(doc_path, state_path=state_path, mode="dictionary")
        assert result.edges_added == 3, f"expected 3 edges, got {result.edges_added}"

        state = load_state(state_path)
        rel_types = {e.relation_type for e in state.edges}
        assert "depends_on" in rel_types
        print(f"  [PASS] ingest_document_extracts_relationships: edges_added={result.edges_added}")


def test_ingest_persistence_roundtrip():
    """Relationships must survive save + load."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "doc.txt")
        with open(doc_path, "w") as f:
            f.write("A car is a vehicle.\n")

        ingest_document(doc_path, state_path=state_path, mode="dictionary")
        state = load_state(state_path)

        assert len(state.edges) >= 1
        edge = state.edges[0]
        assert edge.relation_type == "is_a"
        assert len(edge.provenance) >= 1
        assert edge.provenance[0].extraction_method == "relationship_extractor"
        print("  [PASS] ingest_persistence_roundtrip")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── normalizer", [test_normalize_basic, test_normalize_collapse_whitespace]),
        ("── patterns", [test_pattern_times, test_pattern_rate_of_change,
                         test_pattern_is_a_article, test_no_match]),
        ("── extractor", [test_example1_force, test_example2_acceleration,
                          test_example3_car, test_example4_no_relationships,
                          test_multi_sentence]),
        ("── edge_builder", [test_edge_builder_creates_nodes_and_edges,
                             test_edge_builder_deduplicates]),
        ("── integration", [test_ingest_document_extracts_relationships,
                            test_ingest_persistence_roundtrip]),
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
