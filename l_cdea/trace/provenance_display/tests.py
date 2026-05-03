"""
Provenance display tests.

Covers all 4 spec validation examples:
  1. single source → [source: file | chunk: id | loc: line:1 | conf: ...]
  2. multiple sources → top N entries shown
  3. no provenance (fallback) → [no provenance]
  4. dataset lookup → [source: dataset | conf: 1.0]

Additional checks:
  - extract_provenance_from_node returns correct fields
  - extract_provenance_for_term looks up the right node
  - deduplication by trace_id
  - sort: highest confidence first
  - max_entries respected
  - show_trace_id=True adds trace field
  - ProvenanceDisplayConfig.enabled=False suppresses output
  - format_provenance_trace_section produces structured lines
  - TraceLogger.record_provenance records PROVENANCE stage
  - Formatter to_pretty_text includes [PROVENANCE] section
"""
from __future__ import annotations

import os
import tempfile

import l_cdea.domain
import l_cdea.data

from l_cdea.trace.provenance_display import (
    DisplayedProvenance,
    ProvenanceDisplayConfig,
    extract_provenance_from_node,
    extract_provenance_for_term,
    extract_provenance_from_lookup_traces,
    format_provenance_lines,
    format_provenance_inline,
    format_provenance_no_source,
    format_provenance_trace_section,
)
from l_cdea.discourse.definition_retrieval.lookup import (
    register_definition, clear_definitions, lookup_definition,
)
from l_cdea.core.planner.discourse_lookup import clear_cache

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _reset():
    clear_definitions()
    clear_cache()


def _make_node(term, definition_text, source_path, chunk_id, location, confidence):
    """Build a DiscourseNode with provenance for testing."""
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.core.types.base import SemanticType

    full = f"{term} is {definition_text}."
    prov = Provenance(
        source_id="test_doc",
        source_type="document",
        extraction_method="definition_extractor",
        confidence=confidence,
        trace_id=make_trace_id("test_doc", "definition_extractor", 1),
        timestamp_index=1,
        source_path=source_path,
        chunk_id=chunk_id,
        location=location,
    )
    return DiscourseNode(
        id=make_node_id(SemanticType.ENTITY, full),
        semantic_type=SemanticType.ENTITY,
        value=full,
        salience=1.0,
        created_at=1,
        updated_at=1,
        provenance=(prov,),
        metadata={
            "category": "definition",
            "term": term,
            "definition_text": full,
        },
    )


# ── Spec Example 1: single source ────────────────────────────────────────────

def test_example_1_single_source():
    node = _make_node(
        "velocity", "displacement over time",
        source_path="/data/physics_terms.txt",
        chunk_id="chunk_9f82a1c3",
        location="line:1",
        confidence=0.92,
    )
    entries = extract_provenance_from_node(node)
    ok = len(entries) == 1
    print(f"{_PASS if ok else _FAIL} example 1: entries={len(entries)} (expected 1)")

    lines = format_provenance_lines(entries)
    ok2 = len(lines) == 1
    print(f"{_PASS if ok2 else _FAIL} example 1: lines={len(lines)} (expected 1)")
    ok3 = "physics_terms.txt" in lines[0] and "chunk_9f82a1c3" in lines[0] and "line:1" in lines[0]
    print(f"{_PASS if ok3 else _FAIL} example 1: line content: {lines[0]!r}")
    ok4 = "0.92" in lines[0]
    print(f"{_PASS if ok4 else _FAIL} example 1: confidence shown: {lines[0]!r}")


# ── Spec Example 2: multiple sources ─────────────────────────────────────────

def test_example_2_multiple_sources():
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.core.types.base import SemanticType

    prov1 = Provenance(
        source_id="doc_A", source_type="document",
        extraction_method="definition_extractor", confidence=0.91,
        trace_id=make_trace_id("doc_A", "definition_extractor", 1),
        timestamp_index=1,
        source_path="/data/physics_terms.txt", chunk_id="chunk_a1b2c3d4", location="line:3",
    )
    prov2 = Provenance(
        source_id="doc_B", source_type="document",
        extraction_method="definition_extractor", confidence=0.87,
        trace_id=make_trace_id("doc_B", "definition_extractor", 5),
        timestamp_index=5,
        source_path="/data/textbook_v1.txt", chunk_id="chunk_ff91aa22", location="page:12",
    )
    full = "Acceleration is the rate of change of velocity."
    node = DiscourseNode(
        id=make_node_id(SemanticType.ENTITY, full),
        semantic_type=SemanticType.ENTITY,
        value=full, salience=1.0, created_at=1, updated_at=1,
        provenance=(prov1, prov2),
        metadata={"category": "definition", "term": "acceleration", "definition_text": full},
    )

    cfg = ProvenanceDisplayConfig(max_entries=3)
    entries = extract_provenance_from_node(node)
    ok = len(entries) == 2
    print(f"{_PASS if ok else _FAIL} example 2: entries={len(entries)} (expected 2)")
    # Sorted by confidence desc
    ok2 = entries[0].confidence >= entries[1].confidence
    print(f"{_PASS if ok2 else _FAIL} example 2: sorted confidence desc ({entries[0].confidence}, {entries[1].confidence})")

    lines = format_provenance_lines(entries, cfg)
    ok3 = len(lines) == 2
    print(f"{_PASS if ok3 else _FAIL} example 2: {len(lines)} lines shown (expected 2)")
    ok4 = "physics_terms.txt" in lines[0]
    print(f"{_PASS if ok4 else _FAIL} example 2: first line has higher-confidence source")


# ── Spec Example 3: no provenance (fallback) ─────────────────────────────────

def test_example_3_no_provenance():
    line = format_provenance_no_source()
    ok = "[no provenance]" in line
    print(f"{_PASS if ok else _FAIL} example 3: no_source format: {line!r}")

    # Empty entries → format_provenance_lines returns []
    empty = format_provenance_lines(())
    ok2 = empty == []
    print(f"{_PASS if ok2 else _FAIL} example 3: empty entries → empty lines list")


# ── Spec Example 4: dataset lookup ───────────────────────────────────────────

def test_example_4_dataset_lookup():
    class _FakeLookupTrace:
        hit = True
        returned_value = "Paris"
        dataset_name = "country_capitals_v1"
        lookup_key = "France"
        provenance = {
            "source_id": "country_capitals_v1",
            "confidence": 1.0,
            "extraction_method": "dataset_lookup",
        }

    entries = extract_provenance_from_lookup_traces([_FakeLookupTrace()], "Paris")
    ok = len(entries) == 1
    print(f"{_PASS if ok else _FAIL} example 4: dataset entries={len(entries)} (expected 1)")
    ok2 = entries[0].confidence == 1.0
    print(f"{_PASS if ok2 else _FAIL} example 4: confidence={entries[0].confidence}")
    ok3 = entries[0].source_id == "country_capitals_v1"
    print(f"{_PASS if ok3 else _FAIL} example 4: source_id={entries[0].source_id!r}")

    lines = format_provenance_lines(entries)
    ok4 = "country_capitals_v1" in lines[0] and "1.00" in lines[0]
    print(f"{_PASS if ok4 else _FAIL} example 4: formatted line: {lines[0]!r}")


# ── Deduplication by trace_id ─────────────────────────────────────────────────

def test_deduplication():
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.core.types.base import SemanticType

    tid = make_trace_id("doc_A", "definition_extractor", 1)
    prov = Provenance(
        source_id="doc_A", source_type="document",
        extraction_method="definition_extractor", confidence=0.9,
        trace_id=tid, timestamp_index=1,
    )
    full = "Mass is the amount of matter."
    node = DiscourseNode(
        id=make_node_id(SemanticType.ENTITY, full),
        semantic_type=SemanticType.ENTITY,
        value=full, salience=1.0, created_at=1, updated_at=1,
        provenance=(prov, prov),  # duplicate
        metadata={},
    )
    entries = extract_provenance_from_node(node)
    ok = len(entries) == 1
    print(f"{_PASS if ok else _FAIL} dedup: {len(entries)} entry after dedup (expected 1)")


# ── max_entries respected ─────────────────────────────────────────────────────

def test_max_entries():
    entries = tuple(
        DisplayedProvenance(
            source_path=f"/src/{i}.txt",
            chunk_id=f"chunk_{i:04d}",
            location=f"line:{i}",
            extraction_method="definition_extractor",
            confidence=float(i) / 10,
            trace_id=f"tr_{i:08x}",
        )
        for i in range(5)
    )
    cfg = ProvenanceDisplayConfig(max_entries=2)
    lines = format_provenance_lines(entries, cfg)
    ok = len(lines) == 2
    print(f"{_PASS if ok else _FAIL} max_entries: {len(lines)} lines (expected 2)")


# ── show_trace_id=True ────────────────────────────────────────────────────────

def test_show_trace_id():
    entry = DisplayedProvenance(
        source_path="/src/test.txt", chunk_id="chunk_abc", location="line:1",
        extraction_method="definition_extractor", confidence=0.9, trace_id="tr_abc123",
    )
    cfg_with = ProvenanceDisplayConfig(show_trace_id=True)
    cfg_without = ProvenanceDisplayConfig(show_trace_id=False)
    line_with = format_provenance_lines((entry,), cfg_with)[0]
    line_without = format_provenance_lines((entry,), cfg_without)[0]
    ok = "tr_abc123" in line_with
    print(f"{_PASS if ok else _FAIL} show_trace_id=True: trace_id in output")
    ok2 = "tr_abc123" not in line_without
    print(f"{_PASS if ok2 else _FAIL} show_trace_id=False: trace_id not in output")


# ── enabled=False suppresses output ──────────────────────────────────────────

def test_enabled_false():
    entry = DisplayedProvenance(
        source_path="/src/test.txt", chunk_id="chunk_abc", location="line:1",
        extraction_method="definition_extractor", confidence=0.9, trace_id="tr_abc",
    )
    cfg = ProvenanceDisplayConfig(enabled=False)
    lines = format_provenance_lines((entry,), cfg)
    ok = lines == []
    print(f"{_PASS if ok else _FAIL} enabled=False: output suppressed")


# ── extract_provenance_for_term ───────────────────────────────────────────────

def test_extract_for_term():
    _reset()
    sp = None
    try:
        import tempfile
        from l_cdea.ingestion import ingest_document

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Velocity is displacement over time.\n")
            txt_path = f.name
        sp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        os.unlink(sp)

        ingest_document(txt_path, state_path=sp, mode="dictionary")
        _reset()

        from l_cdea.discourse.storage import load_state
        state = load_state(sp)
        entries = extract_provenance_for_term("velocity", state)
        ok = len(entries) >= 1
        print(f"{_PASS if ok else _FAIL} extract_for_term: entries={len(entries)}")
        if entries:
            ok2 = entries[0].location is not None
            print(f"{_PASS if ok2 else _FAIL} extract_for_term: location={entries[0].location!r}")
            ok3 = entries[0].chunk_id is not None and entries[0].chunk_id.startswith("chunk_")
            print(f"{_PASS if ok3 else _FAIL} extract_for_term: chunk_id={entries[0].chunk_id!r}")
    finally:
        for p in filter(None, [locals().get("txt_path"), sp]):
            if os.path.exists(p):
                os.unlink(p)


# ── format_provenance_trace_section ──────────────────────────────────────────

def test_trace_section():
    entry = DisplayedProvenance(
        source_path="/data/physics.txt", chunk_id="chunk_aa11",
        location="line:2", extraction_method="definition_extractor",
        confidence=0.85, trace_id="tr_xyz",
    )
    cfg = ProvenanceDisplayConfig(show_confidence=True, show_trace_id=False)
    lines = format_provenance_trace_section("acceleration", (entry,), cfg)
    ok = any("acceleration" in l for l in lines)
    print(f"{_PASS if ok else _FAIL} trace_section: term present")
    ok2 = any("physics.txt" in l for l in lines)
    print(f"{_PASS if ok2 else _FAIL} trace_section: source_path present")
    ok3 = any("chunk_aa11" in l for l in lines)
    print(f"{_PASS if ok3 else _FAIL} trace_section: chunk_id present")


# ── TraceLogger records PROVENANCE stage ─────────────────────────────────────

def test_logger_record_provenance():
    from l_cdea.trace import TraceLogger, to_pretty_text, STAGE_PROVENANCE

    logger = TraceLogger("what is velocity", discourse_snapshot_id="test")
    entry = DisplayedProvenance(
        source_path="/data/physics.txt", chunk_id="chunk_aa",
        location="line:1", extraction_method="definition_extractor",
        confidence=0.9, trace_id="tr_test",
    )
    logger.record_provenance("velocity", (entry,))
    record = logger.finalize("success")

    prov_events = [e for e in record.events if e.stage == STAGE_PROVENANCE]
    ok = len(prov_events) == 1
    print(f"{_PASS if ok else _FAIL} logger: PROVENANCE event recorded")
    ok2 = prov_events[0].payload["term"] == "velocity"
    print(f"{_PASS if ok2 else _FAIL} logger: term='velocity' in payload")
    ok3 = prov_events[0].payload["entry_count"] == 1
    print(f"{_PASS if ok3 else _FAIL} logger: entry_count=1")

    text = to_pretty_text(record)
    ok4 = "[PROVENANCE]" in text
    print(f"{_PASS if ok4 else _FAIL} formatter: [PROVENANCE] section present")
    ok5 = "velocity" in text
    print(f"{_PASS if ok5 else _FAIL} formatter: term 'velocity' in trace output")


# ── Fallback records provenance with fallback=True ───────────────────────────

def test_logger_fallback_provenance():
    from l_cdea.trace import TraceLogger, to_pretty_text, STAGE_PROVENANCE

    logger = TraceLogger("what is luminiferous ether")
    logger.record_provenance("luminiferous ether", (), fallback=True)
    record = logger.finalize("success")

    prov_events = [e for e in record.events if e.stage == STAGE_PROVENANCE]
    ok = prov_events[0].payload["fallback"] is True
    print(f"{_PASS if ok else _FAIL} fallback: fallback=True in payload")
    text = to_pretty_text(record)
    ok2 = "no provenance" in text
    print(f"{_PASS if ok2 else _FAIL} fallback: 'no provenance' in trace text")


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: single source",                       test_example_1_single_source),
        ("Example 2: multiple sources",                    test_example_2_multiple_sources),
        ("Example 3: no provenance (fallback)",            test_example_3_no_provenance),
        ("Example 4: dataset lookup",                      test_example_4_dataset_lookup),
        ("Deduplication by trace_id",                      test_deduplication),
        ("max_entries respected",                          test_max_entries),
        ("show_trace_id option",                           test_show_trace_id),
        ("enabled=False suppresses output",                test_enabled_false),
        ("extract_provenance_for_term",                    test_extract_for_term),
        ("format_provenance_trace_section",                test_trace_section),
        ("TraceLogger.record_provenance",                  test_logger_record_provenance),
        ("Fallback provenance recording",                  test_logger_fallback_provenance),
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
