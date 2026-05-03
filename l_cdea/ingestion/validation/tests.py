"""
Knowledge import validation tests.

Covers all 4 spec validation examples:
  1. Accept   — high-confidence definition, no existing discourse nodes
  2. Duplicate — "Paris" already in discourse → status = merge
  3. Conflict  — same chunk/source, different value → status = conflict
  4. Reject    — low confidence + missing optional fields → score < threshold

Additional checks:
  - Scoring: dataset > execution > document weights
  - Canonical duplicate (lowercase match)
  - ValidationDecision invalid status rejected
  - validate_with_trace populates all trace fields
  - validate_batch processes multiple values
  - Determinism: same inputs → same decision
  - No DiscourseState mutation during validation
  - Conflict requires chunk_id; no chunk_id → no false conflict
"""
from __future__ import annotations

from l_cdea.discourse.state import DiscourseState, create_empty
from l_cdea.discourse.node import DiscourseNode
from l_cdea.discourse.memory_graph import add_node
from l_cdea.discourse.node import make_node_id
from l_cdea.core.types.base import SemanticType
from l_cdea.discourse.provenance.model import Provenance, ProvenancedValue, make_trace_id
from l_cdea.ingestion.validation import (
    validate,
    validate_with_trace,
    validate_batch,
    ValidationDecision,
    ValidatedKnowledge,
    ValidationTrace,
    compute_score,
    detect_duplicate,
    detect_conflict,
    REJECT_THRESHOLD,
)
from l_cdea.ingestion.validation.rules import VALID_STATUSES

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prov(
    source_id="src1",
    source_type="document",
    method="definition_extractor",
    confidence=0.8,
    ts=0,
    chunk_id=None,
    source_path=None,
    location=None,
) -> Provenance:
    return Provenance(
        source_id=source_id,
        source_type=source_type,
        extraction_method=method,
        confidence=confidence,
        trace_id=make_trace_id(source_id, method, ts),
        timestamp_index=ts,
        chunk_id=chunk_id,
        source_path=source_path,
        location=location,
    )


def _pv(value, prov: Provenance, sem="entity") -> ProvenancedValue:
    return ProvenancedValue(value=value, semantic_type=sem, provenance=prov)


def _node_with_prov(value, sem_type, prov: Provenance) -> DiscourseNode:
    node_id = make_node_id(sem_type, value)
    return DiscourseNode(
        id=node_id,
        semantic_type=sem_type,
        value=value,
        salience=1.0,
        created_at=0,
        updated_at=0,
        provenance=(prov,),
    )


def _fresh_state() -> DiscourseState:
    return create_empty()


# ── Spec Example 1: accept ────────────────────────────────────────────────────

def test_example_1_accept():
    """High-confidence definition from a document, empty discourse → accept."""
    state = _fresh_state()
    prov = _prov(confidence=0.8, source_type="document", chunk_id="chunk_001")
    value = _pv("rate of change of velocity", prov)

    decision = validate(value, state)
    ok = decision.status == "accept"
    print(f"{_PASS if ok else _FAIL} example 1: status={decision.status!r} (expected 'accept')")
    ok2 = decision.score >= REJECT_THRESHOLD
    print(f"{_PASS if ok2 else _FAIL} example 1: score={decision.score:.3f} ≥ threshold {REJECT_THRESHOLD}")
    ok3 = decision.duplicate_of is None and decision.conflict_with is None
    print(f"{_PASS if ok3 else _FAIL} example 1: no duplicate_of, no conflict_with")


# ── Spec Example 2: duplicate → merge ────────────────────────────────────────

def test_example_2_duplicate():
    """'Paris' already in discourse → status = merge."""
    state = _fresh_state()
    existing_prov = _prov(source_id="ds1", source_type="dataset", method="dataset_lookup", ts=0)
    node = _node_with_prov("Paris", SemanticType.ENTITY, existing_prov)
    add_node(state, node)

    new_prov = _prov(source_id="doc1", source_type="document", method="definition_extractor", ts=1)
    value = _pv("Paris", new_prov)

    decision = validate(value, state)
    ok = decision.status == "merge"
    print(f"{_PASS if ok else _FAIL} example 2: status={decision.status!r} (expected 'merge')")
    ok2 = decision.duplicate_of == node.id
    print(f"{_PASS if ok2 else _FAIL} example 2: duplicate_of={decision.duplicate_of!r}")
    ok3 = decision.conflict_with is None
    print(f"{_PASS if ok3 else _FAIL} example 2: no conflict_with")


# ── Spec Example 3: conflict ──────────────────────────────────────────────────

def test_example_3_conflict():
    """Same source+chunk+method, different value → status = conflict."""
    state = _fresh_state()
    shared_source = "capitals_doc_v1"
    shared_chunk = "france_capital_chunk"
    shared_method = "definition_extractor"

    existing_prov = _prov(
        source_id=shared_source,
        source_type="document",
        method=shared_method,
        chunk_id=shared_chunk,
        ts=0,
    )
    node = _node_with_prov("Paris", SemanticType.ENTITY, existing_prov)
    add_node(state, node)

    conflicting_prov = _prov(
        source_id=shared_source,
        source_type="document",
        method=shared_method,
        chunk_id=shared_chunk,
        ts=1,
    )
    value = _pv("Lyon", conflicting_prov)

    decision = validate(value, state)
    ok = decision.status == "conflict"
    print(f"{_PASS if ok else _FAIL} example 3: status={decision.status!r} (expected 'conflict')")
    ok2 = decision.conflict_with == node.id
    print(f"{_PASS if ok2 else _FAIL} example 3: conflict_with={decision.conflict_with!r}")
    ok3 = decision.duplicate_of is None
    print(f"{_PASS if ok3 else _FAIL} example 3: no duplicate_of")


# ── Spec Example 4: reject ────────────────────────────────────────────────────

def test_example_4_reject():
    """Very low confidence, no optional fields → score < 0.5 → reject."""
    state = _fresh_state()
    # confidence=0.1, document (weight 0.6), no optional fields
    # score = 0.7*0.1 + 0.2*0.6 + 0.1*0.0 = 0.07 + 0.12 = 0.19
    prov = _prov(confidence=0.1, source_type="document", method="heuristic_v1")
    value = _pv("some malformed extraction", prov)

    decision = validate(value, state)
    ok = decision.status == "reject"
    print(f"{_PASS if ok else _FAIL} example 4: status={decision.status!r} (expected 'reject')")
    ok2 = decision.score < REJECT_THRESHOLD
    print(f"{_PASS if ok2 else _FAIL} example 4: score={decision.score:.3f} < threshold {REJECT_THRESHOLD}")


# ── Scoring: source type weights ──────────────────────────────────────────────

def test_scoring_source_weights():
    """dataset > execution > document at equal confidence."""
    base_prov = dict(confidence=0.7, ts=0)
    ds  = _pv("v", _prov(source_type="dataset",   **base_prov))
    ex  = _pv("v", _prov(source_type="execution", **base_prov))
    doc = _pv("v", _prov(source_type="document",  **base_prov))

    s_ds  = compute_score(ds)
    s_ex  = compute_score(ex)
    s_doc = compute_score(doc)

    ok = s_ds > s_ex > s_doc
    print(f"{_PASS if ok else _FAIL} scoring: dataset({s_ds:.3f}) > execution({s_ex:.3f}) > document({s_doc:.3f})")


def test_scoring_completeness_bonus():
    """More optional fields → higher score."""
    prov_sparse = _prov(confidence=0.7, source_type="document")
    prov_rich   = _prov(confidence=0.7, source_type="document",
                        chunk_id="c1", source_path="/doc.txt", location="p.1")

    s_sparse = compute_score(_pv("v", prov_sparse))
    s_rich   = compute_score(_pv("v", prov_rich))

    ok = s_rich > s_sparse
    print(f"{_PASS if ok else _FAIL} scoring completeness: rich({s_rich:.3f}) > sparse({s_sparse:.3f})")


# ── Canonical duplicate (case-insensitive) ────────────────────────────────────

def test_canonical_duplicate():
    """'paris' (lowercase) detected as duplicate of 'Paris' (title case)."""
    state = _fresh_state()
    existing_prov = _prov(source_id="ds1", ts=0)
    node = _node_with_prov("Paris", SemanticType.ENTITY, existing_prov)
    add_node(state, node)

    new_prov = _prov(source_id="doc1", ts=1)
    value = _pv("paris", new_prov)
    duplicate_id = detect_duplicate(value, state)
    ok = duplicate_id == node.id
    print(f"{_PASS if ok else _FAIL} canonical duplicate: 'paris' matches 'Paris'")


# ── No conflict without chunk_id ──────────────────────────────────────────────

def test_no_conflict_without_chunk_id():
    """Conflict detection requires chunk_id; missing chunk_id → no false conflict."""
    state = _fresh_state()
    existing_prov = _prov(source_id="src1", chunk_id="chunk1", ts=0)
    node = _node_with_prov("Paris", SemanticType.ENTITY, existing_prov)
    add_node(state, node)

    # new value from same source but NO chunk_id
    new_prov = _prov(source_id="src1", chunk_id=None, ts=1)
    value = _pv("Lyon", new_prov)
    conflict_id = detect_conflict(value, state)
    ok = conflict_id is None
    print(f"{_PASS if ok else _FAIL} no false conflict without chunk_id: conflict_with={conflict_id!r}")


# ── validate_with_trace ───────────────────────────────────────────────────────

def test_validate_with_trace():
    """validate_with_trace populates all trace fields correctly."""
    state = _fresh_state()
    prov = _prov(confidence=0.85, source_type="dataset", method="dataset_lookup", ts=0)
    value = _pv("Tokyo", prov)

    decision, trace = validate_with_trace(value, state)
    ok = isinstance(trace, ValidationTrace)
    print(f"{_PASS if ok else _FAIL} validate_with_trace: returns ValidationTrace")
    ok2 = trace.input_value == "Tokyo"
    print(f"{_PASS if ok2 else _FAIL} trace.input_value={trace.input_value!r}")
    ok3 = trace.decision == decision.status
    print(f"{_PASS if ok3 else _FAIL} trace.decision={trace.decision!r} matches decision.status")
    ok4 = trace.score == decision.score
    print(f"{_PASS if ok4 else _FAIL} trace.score={trace.score:.3f} matches decision.score")
    ok5 = trace.reason == decision.reason
    print(f"{_PASS if ok5 else _FAIL} trace.reason preserved")


# ── validate_batch ────────────────────────────────────────────────────────────

def test_validate_batch():
    """validate_batch returns one ValidatedKnowledge per input."""
    state = _fresh_state()
    values = tuple([
        _pv("Tokyo",  _prov(confidence=0.9, source_type="dataset", ts=0)),
        _pv("Berlin", _prov(confidence=0.8, source_type="dataset", ts=1)),
        _pv("bad",    _prov(confidence=0.05, source_type="document", ts=2)),
    ])
    results = validate_batch(values, state)

    ok = len(results) == 3
    print(f"{_PASS if ok else _FAIL} validate_batch: {len(results)} results for 3 inputs")
    ok2 = all(isinstance(r, ValidatedKnowledge) for r in results)
    print(f"{_PASS if ok2 else _FAIL} validate_batch: all results are ValidatedKnowledge")
    ok3 = results[0].decision.status == "accept"
    print(f"{_PASS if ok3 else _FAIL} validate_batch[0]: {results[0].decision.status!r}")
    ok4 = results[2].decision.status == "reject"
    print(f"{_PASS if ok4 else _FAIL} validate_batch[2]: {results[2].decision.status!r}")


# ── Determinism ───────────────────────────────────────────────────────────────

def test_validate_deterministic():
    """Same inputs always produce the same ValidationDecision."""
    state = _fresh_state()
    prov = _prov(confidence=0.75, source_type="execution", ts=0)
    value = _pv("result_A", prov)

    d1 = validate(value, state)
    d2 = validate(value, state)
    ok = d1 == d2
    print(f"{_PASS if ok else _FAIL} determinism: same input → same decision ({d1.status!r})")


# ── DiscourseState not mutated ────────────────────────────────────────────────

def test_no_state_mutation():
    """validate() must not add nodes or edges to DiscourseState."""
    state = _fresh_state()
    before_node_count = len(state.nodes)
    before_edge_count = len(state.edges)

    prov = _prov(confidence=0.9, source_type="dataset", ts=0)
    value = _pv("SomeValue", prov)
    validate(value, state)

    ok = len(state.nodes) == before_node_count
    print(f"{_PASS if ok else _FAIL} no state mutation: node count unchanged ({before_node_count})")
    ok2 = len(state.edges) == before_edge_count
    print(f"{_PASS if ok2 else _FAIL} no state mutation: edge count unchanged ({before_edge_count})")


# ── ValidationDecision invalid status ────────────────────────────────────────

def test_invalid_decision_status():
    """ValidationDecision raises ValueError for unknown status."""
    try:
        ValidationDecision(
            status="BOGUS", reason="test", score=0.5,
            duplicate_of=None, conflict_with=None,
        )
        print(f"{_FAIL} invalid status should have raised ValueError")
    except ValueError:
        print(f"{_PASS} ValidationDecision: invalid status raises ValueError")


# ── Conflict priority over duplicate ─────────────────────────────────────────

def test_conflict_takes_priority_over_duplicate():
    """
    If detect_duplicate and detect_conflict both fire, conflict wins
    (per rule priority: conflict > merge > reject > accept).
    """
    state = _fresh_state()
    shared_source = "src_x"
    shared_chunk = "chunk_x"
    shared_method = "definition_extractor"

    # Existing node with "Paris" from the shared chunk
    existing_prov = _prov(
        source_id=shared_source, chunk_id=shared_chunk,
        method=shared_method, ts=0,
    )
    paris_node = _node_with_prov("Paris", SemanticType.ENTITY, existing_prov)
    add_node(state, paris_node)

    # New value "Lyon" — same chunk, so conflict; different value, so not duplicate
    new_prov = _prov(
        source_id=shared_source, chunk_id=shared_chunk,
        method=shared_method, ts=1,
    )
    value = _pv("Lyon", new_prov)
    decision = validate(value, state)
    ok = decision.status == "conflict"
    print(f"{_PASS if ok else _FAIL} conflict priority: status={decision.status!r}")


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: accept",                           test_example_1_accept),
        ("Example 2: duplicate → merge",                test_example_2_duplicate),
        ("Example 3: conflict",                         test_example_3_conflict),
        ("Example 4: reject (low quality)",             test_example_4_reject),
        ("Scoring: source type weights",                test_scoring_source_weights),
        ("Scoring: completeness bonus",                 test_scoring_completeness_bonus),
        ("Canonical duplicate (case-insensitive)",      test_canonical_duplicate),
        ("No conflict without chunk_id",                test_no_conflict_without_chunk_id),
        ("validate_with_trace fields",                  test_validate_with_trace),
        ("validate_batch",                              test_validate_batch),
        ("Determinism",                                 test_validate_deterministic),
        ("No DiscourseState mutation",                  test_no_state_mutation),
        ("Invalid ValidationDecision status",           test_invalid_decision_status),
        ("Conflict priority over duplicate",            test_conflict_takes_priority_over_duplicate),
    ]
    failed = 0
    for name, fn in tests:
        print(f"\n── {name}")
        try:
            fn()
        except Exception as exc:
            print(f"{_FAIL} UNEXPECTED EXCEPTION: {exc!r}")
            failed += 1
    print(f"\n{'All tests passed.' if not failed else f'{failed} test(s) raised unexpected exceptions.'}")


if __name__ == "__main__":
    run_all()
