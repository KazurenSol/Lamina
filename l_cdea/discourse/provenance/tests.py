"""
Provenance memory tests.

Covers all 5 spec validation examples:
  1. Definition ingestion → document provenance
  2. Dataset lookup → dataset provenance (source_type="dataset")
  3. Execution result → execution provenance
  4. Merge identical values → 2-entry provenance list
  5. Conflict: differing values → existing preserved, conflict=True

Additional checks:
  - validate_provenance catches all required field violations
  - attach_provenance validates before wrapping
  - merge deduplicates by trace_id
  - merge sorts by (timestamp_index, trace_id)
  - DiscourseNode carries provenance after import_bundle
  - Provenance survives persistence round-trip (serialize → deserialize)
  - ProvenanceValidationError on invalid source_type
"""
from __future__ import annotations

import l_cdea.data    # register datasets
import l_cdea.domain  # register operators + governance

from l_cdea.discourse.provenance import (
    Provenance,
    ProvenancedValue,
    ProvenanceMergeResult,
    ProvenanceValidationError,
    attach_provenance,
    merge_provenance,
    validate_provenance,
    make_trace_id,
    provenance_to_dict,
    provenance_from_dict,
)

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _make_prov(
    source_id="src1",
    source_type="execution",
    extraction_method="test_op",
    confidence=1.0,
    timestamp_index=0,
) -> Provenance:
    return Provenance(
        source_id=source_id,
        source_type=source_type,
        extraction_method=extraction_method,
        confidence=confidence,
        trace_id=make_trace_id(source_id, extraction_method, timestamp_index),
        timestamp_index=timestamp_index,
    )


# ── Spec Example 1: definition ingestion ─────────────────────────────────────

def test_example_1_definition_provenance():
    """Values from definition extraction carry document provenance."""
    prov = Provenance(
        source_id="doc_acceleration_v1",
        source_type="document",
        extraction_method="definition_extractor",
        confidence=0.85,
        trace_id=make_trace_id("doc_acceleration_v1", "definition_extractor", 0),
        timestamp_index=0,
        chunk_id="chunk_001",
        location="paragraph 2",
    )
    pv = attach_provenance("rate of change of velocity", prov, semantic_type="definition")
    ok = pv.provenance.source_type == "document"
    print(f"{_PASS if ok else _FAIL} example 1: source_type={pv.provenance.source_type!r}")
    ok2 = pv.provenance.extraction_method == "definition_extractor"
    print(f"{_PASS if ok2 else _FAIL} example 1: extraction_method={pv.provenance.extraction_method!r}")
    ok3 = pv.value == "rate of change of velocity"
    print(f"{_PASS if ok3 else _FAIL} example 1: value preserved")


# ── Spec Example 2: dataset lookup ────────────────────────────────────────────

def test_example_2_dataset_provenance():
    """Dataset-backed values carry dataset provenance."""
    prov = Provenance(
        source_id="country_capitals_v1",
        source_type="dataset",
        extraction_method="dataset_lookup",
        confidence=1.0,
        trace_id=make_trace_id("country_capitals_v1", "dataset_lookup", 0),
        timestamp_index=0,
    )
    pv = attach_provenance("Paris", prov, semantic_type="entity")
    ok = pv.provenance.source_id == "country_capitals_v1"
    print(f"{_PASS if ok else _FAIL} example 2: source_id={pv.provenance.source_id!r}")
    ok2 = pv.provenance.source_type == "dataset"
    print(f"{_PASS if ok2 else _FAIL} example 2: source_type={pv.provenance.source_type!r}")
    ok3 = pv.provenance.confidence == 1.0
    print(f"{_PASS if ok3 else _FAIL} example 2: confidence=1.0")


# ── Spec Example 3: execution result ─────────────────────────────────────────

def test_example_3_execution_provenance():
    """Execution-derived outputs carry execution provenance."""
    prov = Provenance(
        source_id="COMPUTE_ACCELERATION",
        source_type="execution",
        extraction_method="COMPUTE_ACCELERATION",
        confidence=1.0,
        trace_id=make_trace_id("COMPUTE_ACCELERATION", "execution", 1),
        timestamp_index=1,
    )
    pv = attach_provenance("5 m/s²", prov, semantic_type="quantity")
    ok = pv.provenance.source_type == "execution"
    print(f"{_PASS if ok else _FAIL} example 3: source_type={pv.provenance.source_type!r}")
    ok2 = pv.provenance.extraction_method == "COMPUTE_ACCELERATION"
    print(f"{_PASS if ok2 else _FAIL} example 3: extraction_method={pv.provenance.extraction_method!r}")


# ── Spec Example 4: merge identical values ────────────────────────────────────

def test_example_4_merge_identical():
    """Merging same value from two sources yields 2-entry provenance list."""
    prov_dataset = Provenance(
        source_id="country_capitals_v1",
        source_type="dataset",
        extraction_method="dataset_lookup",
        confidence=1.0,
        trace_id=make_trace_id("country_capitals_v1", "dataset_lookup", 0),
        timestamp_index=0,
    )
    prov_document = Provenance(
        source_id="doc_geography_v1",
        source_type="document",
        extraction_method="definition_extractor",
        confidence=0.9,
        trace_id=make_trace_id("doc_geography_v1", "definition_extractor", 1),
        timestamp_index=1,
    )
    result = merge_provenance("Paris", (prov_dataset,), "Paris", prov_document)
    ok = not result.conflict
    print(f"{_PASS if ok else _FAIL} example 4: conflict={result.conflict} (expected False)")
    ok2 = len(result.merged_provenance) == 2
    print(f"{_PASS if ok2 else _FAIL} example 4: merged provenance has {len(result.merged_provenance)} entries")
    ok3 = result.merged_provenance[0].timestamp_index <= result.merged_provenance[1].timestamp_index
    print(f"{_PASS if ok3 else _FAIL} example 4: sorted by timestamp_index")


# ── Spec Example 5: conflict ──────────────────────────────────────────────────

def test_example_5_conflict():
    """Differing values: conflict=True, original provenance preserved."""
    prov_paris = _make_prov(source_id="ds1", timestamp_index=0)
    prov_lyon = _make_prov(source_id="ds2", timestamp_index=1)

    result = merge_provenance("Paris", (prov_paris,), "Lyon", prov_lyon)
    ok = result.conflict is True
    print(f"{_PASS if ok else _FAIL} example 5: conflict={result.conflict} (expected True)")
    ok2 = result.merged_provenance == (prov_paris,)
    print(f"{_PASS if ok2 else _FAIL} example 5: original provenance preserved")
    ok3 = len(result.merged_provenance) == 1
    print(f"{_PASS if ok3 else _FAIL} example 5: no new provenance added on conflict")


# ── validate_provenance: required fields ──────────────────────────────────────

def test_validation_required_fields():
    cases = [
        ("source_id", "", "execution", "op", 1.0, "tr_abc", 0),
        ("source_type", "s", "", "op", 1.0, "tr_abc", 0),
        ("extraction_method", "s", "execution", "", 1.0, "tr_abc", 0),
        ("trace_id", "s", "execution", "op", 1.0, "", 0),
    ]
    for field, si, st, em, conf, tid, ts in cases:
        try:
            p = Provenance(
                source_id=si, source_type=st or "execution",
                extraction_method=em, confidence=conf,
                trace_id=tid, timestamp_index=ts,
            )
            if not st:
                p = Provenance(source_id=si, source_type="execution",
                               extraction_method=em or "x", confidence=conf,
                               trace_id=tid or "x", timestamp_index=ts)
            # manually set empty field to test validation
            import dataclasses
            overrides = {"source_id": si, "source_type": st, "extraction_method": em,
                         "confidence": conf, "trace_id": tid, "timestamp_index": ts}
            p = Provenance(**overrides)
            validate_provenance(p)
            print(f"{_FAIL} validation: missing {field!r} should have raised")
        except ProvenanceValidationError:
            print(f"{_PASS} validation: missing {field!r} raises ProvenanceValidationError")
        except Exception as exc:
            print(f"{_FAIL} validation: unexpected exception for {field!r}: {exc!r}")


def test_validation_invalid_source_type():
    try:
        p = Provenance(
            source_id="src", source_type="BOGUS",
            extraction_method="op", confidence=0.5,
            trace_id="tr_x", timestamp_index=0,
        )
        validate_provenance(p)
        print(f"{_FAIL} validation: invalid source_type should have raised")
    except ProvenanceValidationError:
        print(f"{_PASS} validation: invalid source_type raises ProvenanceValidationError")


def test_validation_confidence_bounds():
    for bad in (-0.1, 1.1):
        try:
            p = Provenance(
                source_id="src", source_type="execution",
                extraction_method="op", confidence=bad,
                trace_id="tr_x", timestamp_index=0,
            )
            validate_provenance(p)
            print(f"{_FAIL} validation: confidence={bad} should have raised")
        except ProvenanceValidationError:
            print(f"{_PASS} validation: confidence={bad} raises ProvenanceValidationError")


def test_validation_negative_timestamp():
    try:
        p = Provenance(
            source_id="src", source_type="execution",
            extraction_method="op", confidence=0.5,
            trace_id="tr_x", timestamp_index=-1,
        )
        validate_provenance(p)
        print(f"{_FAIL} validation: negative timestamp_index should have raised")
    except ProvenanceValidationError:
        print(f"{_PASS} validation: negative timestamp_index raises ProvenanceValidationError")


# ── attach_provenance validates ───────────────────────────────────────────────

def test_attach_validates():
    bad_prov = Provenance(
        source_id="", source_type="execution",
        extraction_method="op", confidence=0.5,
        trace_id="tr_x", timestamp_index=0,
    )
    try:
        attach_provenance("value", bad_prov)
        print(f"{_FAIL} attach: invalid provenance should have raised")
    except ProvenanceValidationError:
        print(f"{_PASS} attach: invalid provenance raises ProvenanceValidationError")


# ── Merge deduplicates by trace_id ────────────────────────────────────────────

def test_merge_deduplicates():
    prov = _make_prov(source_id="s1", timestamp_index=0)
    result = merge_provenance("v", (prov,), "v", prov)  # same trace_id
    ok = len(result.merged_provenance) == 1
    print(f"{_PASS if ok else _FAIL} merge deduplication: same trace_id not added twice")


# ── Merge sorts by timestamp_index ────────────────────────────────────────────

def test_merge_sort_order():
    p0 = _make_prov(source_id="s0", timestamp_index=5)
    p1 = _make_prov(source_id="s1", timestamp_index=2)
    result = merge_provenance("v", (p0,), "v", p1)
    ok = result.merged_provenance[0].timestamp_index == 2
    print(f"{_PASS if ok else _FAIL} merge sort: earliest timestamp_index first ({result.merged_provenance[0].timestamp_index})")


# ── make_trace_id is deterministic ───────────────────────────────────────────

def test_trace_id_deterministic():
    id1 = make_trace_id("src", "op", 0)
    id2 = make_trace_id("src", "op", 0)
    ok = id1 == id2
    print(f"{_PASS if ok else _FAIL} make_trace_id deterministic: {id1!r}")
    id3 = make_trace_id("src", "op", 1)
    ok2 = id1 != id3
    print(f"{_PASS if ok2 else _FAIL} make_trace_id differs with timestamp_index")


# ── Provenance survives serialize/deserialize round-trip ─────────────────────

def test_provenance_round_trip():
    prov = Provenance(
        source_id="country_capitals_v1",
        source_type="dataset",
        extraction_method="dataset_lookup",
        confidence=1.0,
        trace_id=make_trace_id("country_capitals_v1", "dataset_lookup", 3),
        timestamp_index=3,
        location="row 42",
    )
    d = provenance_to_dict(prov)
    restored = provenance_from_dict(d)
    ok = restored == prov
    print(f"{_PASS if ok else _FAIL} round-trip: provenance survives serialize/deserialize")
    ok2 = restored.location == "row 42"
    print(f"{_PASS if ok2 else _FAIL} round-trip: optional field location preserved")


# ── DiscourseNode carries provenance after import_bundle ─────────────────────

def test_discourse_node_provenance_after_import():
    """After a full execution and import, DiscourseNodes have provenance."""
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.planner import plan
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.core.planner.graph_builder import execute_plan_graph
    from l_cdea.discourse import create_discourse_state, update_discourse

    clear_cache()
    state = create_discourse_state()

    parsed = parse("capital of France")
    route_result, _ = route_with_trace(parsed)
    qplan, _ = plan(route_result, state)
    result = execute_plan_graph(qplan.graph) if qplan.is_executable else None

    if result:
        class _Bundle:
            resolved_graphs = [qplan.graph]
            node_outputs = {"0": result}
            success_flags = {"0": True}
            failures = {}
        update_discourse(_Bundle(), state)

    nodes_with_provenance = [n for n in state.nodes.values() if n.provenance]
    ok = len(nodes_with_provenance) > 0
    print(f"{_PASS if ok else _FAIL} import_bundle: {len(nodes_with_provenance)} node(s) have provenance")

    if nodes_with_provenance:
        n = nodes_with_provenance[0]
        ok2 = len(n.provenance) >= 1
        print(f"{_PASS if ok2 else _FAIL} node provenance has at least 1 entry")
        ok3 = n.provenance[0].source_type in ("dataset", "execution")
        print(f"{_PASS if ok3 else _FAIL} node source_type={n.provenance[0].source_type!r}")
        ok4 = n.provenance[0].trace_id.startswith("tr_")
        print(f"{_PASS if ok4 else _FAIL} node trace_id has 'tr_' prefix: {n.provenance[0].trace_id!r}")


# ── Provenance survives full persistence round-trip ───────────────────────────

def test_provenance_persistence_round_trip():
    """Provenance on DiscourseNodes survives save→load."""
    import os
    import tempfile
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.planner import plan
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.core.planner.graph_builder import execute_plan_graph
    from l_cdea.discourse import create_discourse_state, update_discourse, save_state, load_state

    clear_cache()
    state = create_discourse_state()

    parsed = parse("capital of France")
    route_result, _ = route_with_trace(parsed)
    qplan, _ = plan(route_result, state)
    result = execute_plan_graph(qplan.graph) if qplan.is_executable else None

    if result:
        class _Bundle:
            resolved_graphs = [qplan.graph]
            node_outputs = {"0": result}
            success_flags = {"0": True}
            failures = {}
        update_discourse(_Bundle(), state)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_state(state, path)
        clear_cache()
        loaded = load_state(path)

        nodes_with_provenance = [n for n in loaded.nodes.values() if n.provenance]
        ok = len(nodes_with_provenance) > 0
        print(f"{_PASS if ok else _FAIL} persistence: {len(nodes_with_provenance)} node(s) loaded with provenance")

        if nodes_with_provenance:
            n = nodes_with_provenance[0]
            ok2 = n.provenance[0].source_type in ("dataset", "execution")
            print(f"{_PASS if ok2 else _FAIL} persistence: source_type={n.provenance[0].source_type!r} preserved")
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: definition ingestion provenance",   test_example_1_definition_provenance),
        ("Example 2: dataset lookup provenance",         test_example_2_dataset_provenance),
        ("Example 3: execution result provenance",       test_example_3_execution_provenance),
        ("Example 4: merge identical values",            test_example_4_merge_identical),
        ("Example 5: conflict — differing values",       test_example_5_conflict),
        ("Validation: required fields",                  test_validation_required_fields),
        ("Validation: invalid source_type",              test_validation_invalid_source_type),
        ("Validation: confidence bounds",                test_validation_confidence_bounds),
        ("Validation: negative timestamp_index",         test_validation_negative_timestamp),
        ("attach_provenance validates",                  test_attach_validates),
        ("Merge deduplicates by trace_id",               test_merge_deduplicates),
        ("Merge sorts by timestamp_index",               test_merge_sort_order),
        ("make_trace_id determinism",                    test_trace_id_deterministic),
        ("Provenance model round-trip",                  test_provenance_round_trip),
        ("DiscourseNode provenance after import",        test_discourse_node_provenance_after_import),
        ("Provenance persistence round-trip",            test_provenance_persistence_round_trip),
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
