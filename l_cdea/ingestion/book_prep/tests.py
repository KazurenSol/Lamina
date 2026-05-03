"""
Tests for l_cdea.ingestion.book_prep

Covers: book_id determinism, chapter parsing, fallback, manifest I/O,
checkpoint roundtrip, resumable ingestion, idempotency, failure handling,
batch mode='book', section_ids, node metadata.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))

_BOOK_2CH = (
    "Chapter 1\n\n"
    "Force is mass times acceleration, a fundamental physical law.\n\n"
    "Chapter 2\n\n"
    "Velocity is displacement over time, a key kinematic quantity.\n"
)

_BOOK_3CH = (
    "Chapter 1\n\nForce is mass times acceleration, a fundamental physical law.\n\n"
    "Chapter 2\n\nVelocity is displacement over time, a key kinematic quantity.\n\n"
    "Chapter 3\n\nEnergy is the capacity to do work, a conserved physical quantity.\n"
)


# ── parser ────────────────────────────────────────────────────────────────────

def test_book_id_deterministic():
    """Same content + path → same book_id every call."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    b1 = parse_book(_BOOK_2CH, source_path="/books/physics.txt", file_size=200)
    b2 = parse_book(_BOOK_2CH, source_path="/books/physics.txt", file_size=200)
    assert b1.metadata.book_id == b2.metadata.book_id
    print(f"  [PASS] book_id_deterministic: {b1.metadata.book_id}")


def test_book_id_differs_for_different_files():
    """Different content → different book_id."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    b1 = parse_book(_BOOK_2CH, source_path="/a.txt", file_size=100)
    b2 = parse_book("Chapter 1\n\nSomething else entirely.\n", source_path="/b.txt", file_size=50)
    assert b1.metadata.book_id != b2.metadata.book_id
    print("  [PASS] book_id_differs_for_different_files")


def test_parse_book_two_chapters():
    """2 chapter headings → 2 BookChapters."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    bs = parse_book(_BOOK_2CH, source_path="/test.txt", file_size=len(_BOOK_2CH))
    assert len(bs.chapters) == 2, f"expected 2, got {len(bs.chapters)}"
    assert bs.chapters[0].title == "Chapter 1"
    assert bs.chapters[1].title == "Chapter 2"
    print(f"  [PASS] parse_book_two_chapters: {[c.title for c in bs.chapters]}")


def test_parse_book_fallback_no_chapters():
    """No chapter headings → single chapter with title=None."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    text = "Force is mass times acceleration, a fundamental physical law.\n"
    bs = parse_book(text, source_path="/flat.txt", file_size=len(text))
    assert len(bs.chapters) == 1
    assert bs.chapters[0].title is None
    print("  [PASS] parse_book_fallback_no_chapters")


def test_parse_book_chapter_formats():
    """Various chapter heading patterns are detected."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    texts = [
        "CHAPTER ONE\n\nForce is mass times acceleration, a fundamental physical law.\n",
        "Chapter 1: Introduction\n\nForce is mass times acceleration, a fundamental physical law.\n",
        "# Chapter 1\n\nForce is mass times acceleration, a fundamental physical law.\n",
    ]
    for text in texts:
        bs = parse_book(text, source_path="/x.txt", file_size=len(text))
        assert len(bs.chapters) == 1, f"expected 1 chapter for: {text[:30]!r}"
    print("  [PASS] parse_book_chapter_formats")


def test_chapter_section_ids_populated():
    """Each chapter carries section_ids from document_scaling parser."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    text = (
        "Chapter 1\n\n"
        "## Forces\n\nForce is mass times acceleration, a fundamental physical law.\n\n"
        "Chapter 2\n\n"
        "## Kinematics\n\nVelocity is displacement over time, a key kinematic quantity.\n"
    )
    bs = parse_book(text, source_path="/sec.txt", file_size=len(text))
    assert len(bs.chapters) == 2
    for ch in bs.chapters:
        assert len(ch.section_ids) >= 1, f"chapter {ch.title!r} has no section_ids"
    print(f"  [PASS] chapter_section_ids_populated: {[len(c.section_ids) for c in bs.chapters]}")


def test_chapter_line_range():
    """Chapter start_line and end_line correctly bracket chapter content."""
    from l_cdea.ingestion.book_prep.parser import parse_book
    lines = _BOOK_2CH.splitlines()
    bs = parse_book(_BOOK_2CH, source_path="/t.txt", file_size=len(_BOOK_2CH))
    ch1 = bs.chapters[0]
    ch2 = bs.chapters[1]
    assert lines[ch1.start_line].startswith("Chapter 1")
    assert lines[ch2.start_line].startswith("Chapter 2")
    assert ch1.end_line < ch2.start_line
    print(f"  [PASS] chapter_line_range: ch1={ch1.start_line}-{ch1.end_line}, ch2={ch2.start_line}-{ch2.end_line}")


# ── manifest ──────────────────────────────────────────────────────────────────

def test_manifest_save_load_roundtrip():
    """BookManifest survives a save/load cycle."""
    from l_cdea.ingestion.book_prep.manifest import BookManifest, save_manifest, load_manifest
    with tempfile.TemporaryDirectory() as tmp:
        manifests_dir = os.path.join(tmp, "manifests")
        m = BookManifest(
            book_id="abc123",
            source_path="/test.txt",
            chapters_total=3,
            chapters_completed=1,
            chunks_total=10,
            chunks_processed=4,
            nodes_added=2,
            edges_added=3,
            last_checkpoint={"book_id": "abc123", "chapter_id": "chap_x", "chunk_index": 4, "timestamp": 1},
            status="in_progress",
        )
        save_manifest(m, manifests_dir)
        loaded = load_manifest("abc123", manifests_dir)
        assert loaded is not None
        assert loaded.book_id == "abc123"
        assert loaded.chapters_completed == 1
        assert loaded.status == "in_progress"
        assert loaded.last_checkpoint["chapter_id"] == "chap_x"
        print("  [PASS] manifest_save_load_roundtrip")


def test_manifest_atomic_no_tmp_left():
    """No .tmp file remains after save_manifest."""
    from l_cdea.ingestion.book_prep.manifest import BookManifest, save_manifest, manifest_path
    with tempfile.TemporaryDirectory() as tmp:
        manifests_dir = os.path.join(tmp, "manifests")
        m = BookManifest(
            book_id="xyz", source_path="/x.txt",
            chapters_total=1, chapters_completed=0,
            chunks_total=0, chunks_processed=0,
            nodes_added=0, edges_added=0,
            last_checkpoint=None, status="in_progress",
        )
        save_manifest(m, manifests_dir)
        tmp_path = manifest_path("xyz", manifests_dir) + ".tmp"
        assert not os.path.exists(tmp_path), ".tmp file should be removed after atomic save"
        assert os.path.exists(manifest_path("xyz", manifests_dir))
        print("  [PASS] manifest_atomic_no_tmp_left")


def test_manifest_missing_returns_none():
    """load_manifest returns None when no manifest file exists."""
    from l_cdea.ingestion.book_prep.manifest import load_manifest
    with tempfile.TemporaryDirectory() as tmp:
        result = load_manifest("does_not_exist", tmp)
        assert result is None
        print("  [PASS] manifest_missing_returns_none")


def test_manifest_failed_status():
    """status='failed' persists correctly and can be detected."""
    from l_cdea.ingestion.book_prep.manifest import BookManifest, save_manifest, load_manifest
    with tempfile.TemporaryDirectory() as tmp:
        manifests_dir = os.path.join(tmp, "manifests")
        m = BookManifest(
            book_id="fail1", source_path="/f.txt",
            chapters_total=5, chapters_completed=2,
            chunks_total=0, chunks_processed=8,
            nodes_added=4, edges_added=3,
            last_checkpoint=None, status="failed",
        )
        save_manifest(m, manifests_dir)
        loaded = load_manifest("fail1", manifests_dir)
        assert loaded.status == "failed"
        print("  [PASS] manifest_failed_status")


# ── checkpoint ────────────────────────────────────────────────────────────────

def test_checkpoint_roundtrip():
    """Checkpoint serializes and deserializes without loss."""
    from l_cdea.ingestion.book_prep.checkpoint import Checkpoint, checkpoint_to_dict, checkpoint_from_dict
    cp = Checkpoint(book_id="book1", chapter_id="chap_abc", chunk_index=15, timestamp=3)
    d = checkpoint_to_dict(cp)
    cp2 = checkpoint_from_dict(d)
    assert cp == cp2
    print(f"  [PASS] checkpoint_roundtrip: {cp}")


# ── loader ────────────────────────────────────────────────────────────────────

def test_ingest_book_basic():
    """Basic 2-chapter book: manifest complete, chapters and chunks processed."""
    from l_cdea.ingestion.book_prep.loader import ingest_book
    from l_cdea.ingestion.book_prep.manifest import load_manifest
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        manifests_dir = os.path.join(tmp, "manifests")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_2CH)
        trace = ingest_book(book_path, state_path=state_path, manifests_dir=manifests_dir)
        assert trace.chapters_total == 2
        assert trace.chapters_processed == 2
        assert trace.chunks_processed >= 2
        assert not trace.resumed
        m = load_manifest(trace.book_id, manifests_dir)
        assert m is not None
        assert m.status == "complete"
        assert m.chapters_completed == 2
        print(f"  [PASS] ingest_book_basic: chapters={trace.chapters_processed}, "
              f"chunks={trace.chunks_processed}, nodes={trace.nodes_added}")


def test_ingest_book_resume():
    """Interrupt after chapter 1, resume → only chapter 2 processed."""
    from l_cdea.ingestion.book_prep.loader import ingest_book
    from l_cdea.ingestion.book_prep.manifest import load_manifest
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        manifests_dir = os.path.join(tmp, "manifests")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_3CH)

        # First pass: only chapter 1
        t1 = ingest_book(book_path, state_path=state_path, manifests_dir=manifests_dir, max_chapters=1)
        assert t1.chapters_processed == 1
        assert not t1.resumed
        m1 = load_manifest(t1.book_id, manifests_dir)
        assert m1.chapters_completed == 1
        assert m1.status == "in_progress"

        # Second pass: resume
        t2 = ingest_book(book_path, resume=True, state_path=state_path, manifests_dir=manifests_dir)
        assert t2.resumed
        assert t2.chapters_processed == 2  # chapters 2 and 3 only
        m2 = load_manifest(t2.book_id, manifests_dir)
        assert m2.status == "complete"
        assert m2.chapters_completed == 3
        print(f"  [PASS] ingest_book_resume: t1.chapters={t1.chapters_processed}, "
              f"t2.chapters={t2.chapters_processed}, m2.status={m2.status}")


def test_ingest_book_idempotent():
    """Running ingest_book twice on same book produces no duplicate nodes."""
    from l_cdea.ingestion.book_prep.loader import ingest_book
    from l_cdea.discourse.storage import load_state
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        manifests_dir = os.path.join(tmp, "manifests")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_2CH)

        t1 = ingest_book(book_path, state_path=state_path, manifests_dir=manifests_dir)
        state_after_first = load_state(state_path)
        node_count_first = len(state_after_first.nodes)

        # Second run: resume=False forces a fresh manifest pass; nodes already exist
        t2 = ingest_book(book_path, resume=False, state_path=state_path, manifests_dir=manifests_dir)
        state_after_second = load_state(state_path)
        node_count_second = len(state_after_second.nodes)

        assert node_count_second == node_count_first, (
            f"duplicate nodes: first={node_count_first}, second={node_count_second}"
        )
        print(f"  [PASS] ingest_book_idempotent: nodes={node_count_first} (no duplicates)")


def test_ingest_book_node_metadata():
    """Nodes produced by book ingestion carry book_id, chapter_id in metadata."""
    from l_cdea.ingestion.book_prep.loader import ingest_book
    from l_cdea.discourse.storage import load_state
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        manifests_dir = os.path.join(tmp, "manifests")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_2CH)
        trace = ingest_book(book_path, state_path=state_path, manifests_dir=manifests_dir)
        state = load_state(state_path)
        book_nodes = [
            n for n in state.nodes.values()
            if n.metadata and n.metadata.get("book_id") == trace.book_id
        ]
        assert book_nodes, "no nodes with book_id in metadata"
        for node in book_nodes:
            assert node.metadata.get("chapter_id"), f"node {node.id} missing chapter_id"
        print(f"  [PASS] ingest_book_node_metadata: {len(book_nodes)} nodes with book_id")


def test_ingest_book_failure_sets_manifest_failed():
    """An ingestion failure sets manifest.status to 'failed'."""
    from l_cdea.ingestion.book_prep.loader import ingest_book, _ingest_chapter
    from l_cdea.ingestion.book_prep.manifest import load_manifest
    import l_cdea.ingestion.book_prep.loader as loader_mod

    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        manifests_dir = os.path.join(tmp, "manifests")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_2CH)

        # Patch _ingest_chapter to raise on second call
        original = loader_mod._ingest_chapter
        call_count = [0]

        def failing_chapter(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise RuntimeError("simulated chapter failure")
            return original(*args, **kwargs)

        loader_mod._ingest_chapter = failing_chapter
        try:
            try:
                ingest_book(book_path, state_path=state_path, manifests_dir=manifests_dir)
            except RuntimeError:
                pass
        finally:
            loader_mod._ingest_chapter = original

        # Find the manifest file
        manifest_files = os.listdir(manifests_dir) if os.path.exists(manifests_dir) else []
        assert manifest_files, "manifest directory should exist with a file"
        book_id = manifest_files[0].replace(".json", "")
        m = load_manifest(book_id, manifests_dir)
        assert m is not None
        assert m.status == "failed", f"expected 'failed', got {m.status!r}"
        assert m.chapters_completed == 1, f"checkpoint should preserve completed chapter count"
        print(f"  [PASS] ingest_book_failure_sets_manifest_failed: chapters_completed={m.chapters_completed}")


# ── batch mode ────────────────────────────────────────────────────────────────

def test_batch_book_mode():
    """batch_ingest_files with mode='book' calls ingest_book per file."""
    from l_cdea.ingestion.batch.batch import batch_ingest_files
    from l_cdea.ingestion.batch.config import BatchIngestionConfig
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "state.json")
        book_path = os.path.join(tmp, "book.txt")
        with open(book_path, "w") as f:
            f.write(_BOOK_2CH)
        cfg = BatchIngestionConfig(mode="book", state_path=state_path, save_per_file=True)
        report = batch_ingest_files([book_path], cfg)
        assert report.successful_files == 1
        assert report.total_chunks >= 2
        print(f"  [PASS] batch_book_mode: chunks={report.total_chunks}, nodes={report.total_nodes_added}")


# ── trace ─────────────────────────────────────────────────────────────────────

def test_trace_fields():
    """BookIngestionTrace has all required fields."""
    from l_cdea.ingestion.book_prep.trace import BookIngestionTrace
    t = BookIngestionTrace(
        book_id="abc", chapters_total=3, chapters_processed=3,
        chunks_processed=10, nodes_added=4, edges_added=6, resumed=False,
    )
    assert t.book_id == "abc"
    assert t.chapters_total == 3
    assert not t.resumed
    print("  [PASS] trace_fields")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── parser", [
            test_book_id_deterministic,
            test_book_id_differs_for_different_files,
            test_parse_book_two_chapters,
            test_parse_book_fallback_no_chapters,
            test_parse_book_chapter_formats,
            test_chapter_section_ids_populated,
            test_chapter_line_range,
        ]),
        ("── manifest", [
            test_manifest_save_load_roundtrip,
            test_manifest_atomic_no_tmp_left,
            test_manifest_missing_returns_none,
            test_manifest_failed_status,
        ]),
        ("── checkpoint", [
            test_checkpoint_roundtrip,
        ]),
        ("── loader", [
            test_ingest_book_basic,
            test_ingest_book_resume,
            test_ingest_book_idempotent,
            test_ingest_book_node_metadata,
            test_ingest_book_failure_sets_manifest_failed,
        ]),
        ("── batch", [
            test_batch_book_mode,
        ]),
        ("── trace", [
            test_trace_fields,
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
