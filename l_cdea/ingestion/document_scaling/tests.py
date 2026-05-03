"""
Tests for l_cdea.ingestion.document_scaling

Covers all four spec validation examples plus unit tests for parser,
chunker, metadata, confidence boost, and end-to-end ingestion.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))


# ── parser ────────────────────────────────────────────────────────────────────

def test_example1_simple_headings():
    """Example 1: # Mechanics / ## Kinematics → 2 sections, 2 chunks."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = (
        "# Mechanics\n\n"
        "Force is mass times acceleration.\n\n"
        "## Kinematics\n\n"
        "Velocity is displacement over time.\n"
    )
    ds = parse_document(text)
    assert len(ds.sections) == 2, f"expected 2 sections, got {len(ds.sections)}"
    assert ds.sections[0].heading == "Mechanics"
    assert ds.sections[0].level == 1
    assert ds.sections[1].heading == "Kinematics"
    assert ds.sections[1].level == 2
    assert ds.sections[1].parent_id == ds.sections[0].section_id
    # Text content assigned to correct sections
    assert "Force" in ds.sections[0].text
    assert "Velocity" in ds.sections[1].text
    print(f"  [PASS] example1_simple_headings: {[s.heading for s in ds.sections]}")


def test_example2_no_headings():
    """Example 2: plain paragraphs → one section, fallback."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = "Kinetic energy is the energy of motion.\n\nPotential energy depends on position."
    ds = parse_document(text)
    assert len(ds.sections) == 1
    assert ds.sections[0].heading is None
    assert ds.sections[0].level == 0
    assert ds.sections[0].parent_id is None
    print("  [PASS] example2_no_headings")


def test_example3_nested_headings():
    """Example 3: # Physics / ## Mechanics / ### Forces → hierarchy preserved."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = "# Physics\n## Mechanics\n### Forces\n\nForce is a push or pull.\n"
    ds = parse_document(text)
    assert len(ds.sections) == 3
    physics = ds.sections[0]
    mechanics = ds.sections[1]
    forces = ds.sections[2]
    assert physics.level == 1 and physics.parent_id is None
    assert mechanics.level == 2 and mechanics.parent_id == physics.section_id
    assert forces.level == 3 and forces.parent_id == mechanics.section_id
    print(f"  [PASS] example3_nested: {[(s.level, s.heading) for s in ds.sections]}")


def test_heading_detection_all_caps():
    """ALL CAPS line ≤ 10 words → heading level 1."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = "INTRODUCTION\n\nThis section introduces physics."
    ds = parse_document(text)
    assert len(ds.sections) == 1
    assert ds.sections[0].heading == "Introduction"
    assert ds.sections[0].level == 1
    print("  [PASS] heading_detection_all_caps")


def test_heading_detection_colon():
    """Short line ending with ':' → heading level 2."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = "Definitions:\n\nForce is mass times acceleration."
    ds = parse_document(text)
    assert len(ds.sections) == 1
    assert ds.sections[0].heading == "Definitions"
    assert ds.sections[0].level == 2
    print("  [PASS] heading_detection_colon")


def test_section_ids_deterministic():
    """Same document text produces identical section IDs on every call."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    text = "# Physics\n\nForce is mass times acceleration.\n"
    ds1 = parse_document(text)
    ds2 = parse_document(text)
    assert ds1.sections[0].section_id == ds2.sections[0].section_id
    print("  [PASS] section_ids_deterministic")


# ── chunker ───────────────────────────────────────────────────────────────────

def test_chunker_assigns_section_metadata():
    """Each chunk carries section_id and heading from its section."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    text = (
        "# Mechanics\n\n"
        "Force is mass times acceleration.\n\n"
        "## Kinematics\n\n"
        "Velocity is displacement over time.\n"
    )
    ds = parse_document(text)
    chunks, rejected = chunk_structured(ds, source_path="/test/doc.txt", source_title="Test",
                                        min_chunk_chars=20)
    assert len(chunks) == 2
    assert chunks[0].heading == "Mechanics"
    assert chunks[0].section_id == ds.sections[0].section_id
    assert chunks[1].heading == "Kinematics"
    assert chunks[1].section_id == ds.sections[1].section_id
    print(f"  [PASS] chunker_assigns_section_metadata: {[(c.heading, c.paragraph_index) for c in chunks]}")


def test_chunker_location_format():
    """Chunk location = 'section:<id>:para:<idx>'."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    text = "# Forces\n\nForce is mass times acceleration.\n"
    ds = parse_document(text)
    chunks, _ = chunk_structured(ds, source_path="/test/doc.txt", source_title="Test",
                                 min_chunk_chars=20)
    assert len(chunks) == 1, f"expected 1 chunk, got {len(chunks)}"
    loc = chunks[0].location
    assert loc.startswith("section:") and ":para:" in loc
    print(f"  [PASS] chunker_location_format: {loc!r}")


def test_chunker_rejects_short_paragraphs():
    """Paragraphs shorter than min_chunk_chars are rejected."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    text = "# Physics\n\nOK.\n\nForce is mass times acceleration, a key relationship.\n"
    ds = parse_document(text)
    chunks, rejected = chunk_structured(ds, source_path="/t.txt", source_title="T", min_chunk_chars=40)
    assert rejected >= 1
    texts = [c.text for c in chunks]
    assert not any("OK." in t for t in texts)
    print(f"  [PASS] chunker_rejects_short: {len(chunks)} accepted, {rejected} rejected")


def test_chunker_ids_deterministic():
    """Chunk IDs are deterministic for the same source + text."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    text = "# Physics\n\nForce is mass times acceleration.\n"
    ds = parse_document(text)
    c1, _ = chunk_structured(ds, source_path="/doc.txt", source_title="T", min_chunk_chars=20)
    c2, _ = chunk_structured(ds, source_path="/doc.txt", source_title="T", min_chunk_chars=20)
    assert len(c1) == 1 and len(c2) == 1
    assert c1[0].chunk_id == c2[0].chunk_id
    print(f"  [PASS] chunker_ids_deterministic: {c1[0].chunk_id!r}")


# ── metadata & confidence boost ───────────────────────────────────────────────

def test_example4_confidence_boost():
    """Example 4: 'Definitions' heading boosts confidence by 0.1."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    from l_cdea.ingestion.chunker import DocumentChunk
    from l_cdea.ingestion.definition_extractor import extract_definitions
    text = "Definitions:\n\nForce is mass times acceleration, a fundamental physical law.\n"
    ds = parse_document(text)
    chunks, _ = chunk_structured(ds, source_path="/test.txt", source_title="T",
                                 min_chunk_chars=20)
    assert len(chunks) == 1, f"expected 1 chunk, got {len(chunks)}"
    sc = chunks[0]
    dc = DocumentChunk(
        text=sc.text, source_title="T", source_path="/test.txt",
        paragraph_index=sc.paragraph_index,
        chunk_id=sc.chunk_id, location=sc.location,
        section_id=sc.section_id, heading=sc.heading,
    )
    defs = extract_definitions(dc)
    assert len(defs) == 1
    assert defs[0].confidence == 0.9, f"expected 0.9, got {defs[0].confidence}"
    assert defs[0].heading == "Definitions"
    assert defs[0].section_id == sc.section_id
    print(f"  [PASS] example4_confidence_boost: conf={defs[0].confidence}")


def test_no_boost_without_definition_heading():
    """Non-definition heading → base confidence 0.8."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    from l_cdea.ingestion.chunker import DocumentChunk
    from l_cdea.ingestion.definition_extractor import extract_definitions
    text = "# Mechanics\n\nForce is mass times acceleration, a fundamental physical law.\n"
    ds = parse_document(text)
    chunks, _ = chunk_structured(ds, source_path="/t.txt", source_title="T",
                                 min_chunk_chars=20)
    assert len(chunks) == 1, f"expected 1 chunk, got {len(chunks)}"
    sc = chunks[0]
    dc = DocumentChunk(
        text=sc.text, source_title="T", source_path="/t.txt",
        paragraph_index=sc.paragraph_index,
        chunk_id=sc.chunk_id, location=sc.location,
        section_id=sc.section_id, heading=sc.heading,
    )
    defs = extract_definitions(dc)
    assert len(defs) == 1
    assert defs[0].confidence == 0.8, f"expected 0.8, got {defs[0].confidence}"
    print(f"  [PASS] no_boost_mechanics_heading: conf={defs[0].confidence}")


# ── end-to-end ingestion ──────────────────────────────────────────────────────

def test_e2e_document_structured():
    """Full pipeline: ingest structured doc → definitions + relationships extracted."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "physics.txt")
        with open(doc_path, "w") as f:
            f.write("# Mechanics\n\n")
            f.write("Force is mass times acceleration, a fundamental physical relationship.\n\n")
            f.write("## Kinematics\n\n")
            f.write("Acceleration is the rate of change of velocity over time.\n")
        result = ingest_document(doc_path, state_path=state_path, mode="document_structured")
        assert result.sections_detected == 2, f"expected 2 sections, got {result.sections_detected}"
        assert result.chunks_processed == 2, f"expected 2 chunks, got {result.chunks_processed}"
        assert result.definitions >= 2, f"expected ≥2 definitions, got {result.definitions}"
        assert result.edges_added >= 3, f"expected ≥3 edges, got {result.edges_added}"
        print(f"  [PASS] e2e_document_structured: sections={result.sections_detected}, "
              f"chunks={result.chunks_processed}, defs={result.definitions}, edges={result.edges_added}")


def test_e2e_section_metadata_in_state():
    """Nodes created by structured ingestion carry section_id and heading in metadata."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    from l_cdea.discourse.storage import load_state
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "doc.txt")
        with open(doc_path, "w") as f:
            f.write("Definitions:\n\nForce is mass times acceleration, a fundamental physical law.\n")
        ingest_document(doc_path, state_path=state_path, mode="document_structured")
        state = load_state(state_path)
        meta_entries = [n.metadata for n in state.nodes.values() if n.metadata]
        section_ids = [m.get("section_id") for m in meta_entries if m.get("section_id")]
        headings = [m.get("heading") for m in meta_entries if m.get("heading")]
        assert section_ids, "no section_id found in node metadata"
        assert headings, "no heading found in node metadata"
        print(f"  [PASS] e2e_section_metadata: section_ids={section_ids[:1]}, headings={headings[:1]}")


def test_existing_modes_unchanged():
    """dictionary and document modes still work after adding document_structured."""
    from l_cdea.ingestion.knowledge_importer import ingest_document
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ("dictionary", "document"):
            state_path = os.path.join(tmp, f"state_{mode}.json")
            doc_path = os.path.join(tmp, f"{mode}.txt")
            with open(doc_path, "w") as f:
                f.write("Force is mass times acceleration, a fundamental physical law.\n")
            result = ingest_document(doc_path, state_path=state_path, mode=mode)
            assert result.chunks_processed >= 1, f"{mode}: expected chunks"
            print(f"  [PASS] existing_mode_{mode}: chunks={result.chunks_processed}")


def test_batch_report_sections_field():
    """BatchIngestionReport aggregates sections_detected from structured files."""
    from l_cdea.ingestion.batch.batch import batch_ingest_files
    from l_cdea.ingestion.batch.config import BatchIngestionConfig
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        doc_path = os.path.join(tmp, "doc.txt")
        with open(doc_path, "w") as f:
            f.write("# Physics\n\nForce is mass times acceleration, a fundamental physical relationship.\n\n"
                    "## Kinematics\n\nAcceleration is the rate of change of velocity over time.\n")
        cfg = BatchIngestionConfig(
            mode="document_structured",
            state_path=state_path,
            save_per_file=True,
        )
        report = batch_ingest_files([doc_path], cfg)
        assert report.total_sections_detected >= 2, \
            f"expected ≥2 sections, got {report.total_sections_detected}"
        assert report.total_relationships_extracted >= 0
        print(f"  [PASS] batch_report_sections: sections={report.total_sections_detected}, "
              f"rels={report.total_relationships_extracted}")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── parser", [
            test_example1_simple_headings,
            test_example2_no_headings,
            test_example3_nested_headings,
            test_heading_detection_all_caps,
            test_heading_detection_colon,
            test_section_ids_deterministic,
        ]),
        ("── chunker", [
            test_chunker_assigns_section_metadata,
            test_chunker_location_format,
            test_chunker_rejects_short_paragraphs,
            test_chunker_ids_deterministic,
        ]),
        ("── metadata / confidence", [
            test_example4_confidence_boost,
            test_no_boost_without_definition_heading,
        ]),
        ("── end-to-end", [
            test_e2e_document_structured,
            test_e2e_section_metadata_in_state,
            test_existing_modes_unchanged,
            test_batch_report_sections_field,
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
