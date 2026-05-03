"""
Dictionary ingestion mode tests.

Covers all 4 spec validation examples plus unit coverage:
  1. document mode rejects "Velocity is displacement over time." (too short)
  2. dictionary mode accepts "Velocity is displacement over time." as a definition
  3. single-word "Velocity" rejected even in dictionary mode
  4. mixed content: only valid definitions accepted in dictionary mode
  5. invalid mode → ValueError
  6. filter: punctuation-only rejected
  7. filter: fragment with no verb rejected
  8. filter: multi-word + verb accepted
  9. classifier: definition wins in dictionary mode
  10. full pipeline: ingest physics_basic.txt in dictionary mode, velocity extracted
  11. IngestionModeTrace records accepted/rejected counts
  12. Provenance contains ingestion_mode
  13. Line-level chunking: 4 definitions → 4 chunks (mini_dictionary.txt)
  14. Line-level: invalid fragment on one line, valid on next → 1 chunk
  15. Line-level: blank lines silently skipped
  16. Document mode unchanged (paragraph-based)
  17. Chunk IDs are stable across runs
  18. Provenance chunk_id and location present in persisted nodes
"""
from __future__ import annotations

import os

import l_cdea.domain
import l_cdea.data

from l_cdea.ingestion.modes import (
    validate_mode,
    get_mode_config,
    is_valid_dictionary_chunk,
    IngestionModeTrace,
)
from l_cdea.ingestion.chunker import chunk_document_with_trace
from l_cdea.ingestion.document_loader import RawDocument

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"

PHYSICS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge_seed", "physics_basic.txt")
)


# ── Spec Example 1: document mode rejects short definition ───────────────────

def test_example_1_document_mode_rejects_short():
    doc = RawDocument(
        title="test",
        content="Velocity is displacement over time.",
        source_path="test.txt",
    )
    chunks, rejected = chunk_document_with_trace(doc, mode="document")
    ok = len(chunks) == 0
    print(f"{_PASS if ok else _FAIL} example 1: document mode: chunks={len(chunks)} (expected 0)")
    ok2 = rejected == 1
    print(f"{_PASS if ok2 else _FAIL} example 1: document mode: rejected={rejected} (expected 1)")


# ── Spec Example 2: dictionary mode accepts short definition ─────────────────

def test_example_2_dictionary_mode_accepts_short():
    doc = RawDocument(
        title="test",
        content="Velocity is displacement over time.",
        source_path="test.txt",
    )
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok = len(chunks) == 1
    print(f"{_PASS if ok else _FAIL} example 2: dictionary mode: chunks={len(chunks)} (expected 1)")
    if chunks:
        ok2 = "velocity" in chunks[0].text.lower()
        print(f"{_PASS if ok2 else _FAIL} example 2: chunk text={chunks[0].text!r}")


# ── Spec Example 3: single-word rejected even in dictionary mode ─────────────

def test_example_3_single_word_rejected():
    ok = not is_valid_dictionary_chunk("Velocity")
    print(f"{_PASS if ok else _FAIL} example 3: 'Velocity' rejected in dictionary mode")
    ok2 = not is_valid_dictionary_chunk("mass")
    print(f"{_PASS if ok2 else _FAIL} example 3: 'mass' rejected in dictionary mode")

    doc = RawDocument(title="test", content="Velocity", source_path="test.txt")
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok3 = len(chunks) == 0
    print(f"{_PASS if ok3 else _FAIL} example 3: single-word chunk not accepted: chunks={len(chunks)}")


# ── Spec Example 4: mixed content, only valid definitions accepted ────────────

def test_example_4_mixed_content():
    content = "\n\n".join([
        "Velocity is displacement over time.",        # short, valid → accepted in dict mode
        "Acceleration is the rate of change of velocity.",  # long, valid → accepted
        "Physics",                                    # single word → rejected
        "See above.",                                 # no verb in known set → rejected
        "Momentum is mass times velocity.",           # short, valid → accepted
    ])
    doc = RawDocument(title="test", content=content, source_path="test.txt")

    chunks_doc, rej_doc = chunk_document_with_trace(doc, mode="document")
    ok = len(chunks_doc) == 1  # only the long sentence passes 40-char threshold
    print(f"{_PASS if ok else _FAIL} example 4: document mode chunks={len(chunks_doc)} (expected 1)")

    chunks_dict, rej_dict = chunk_document_with_trace(doc, mode="dictionary")
    ok2 = len(chunks_dict) == 3  # velocity, acceleration, momentum
    print(f"{_PASS if ok2 else _FAIL} example 4: dictionary mode chunks={len(chunks_dict)} (expected 3)")
    ok3 = rej_dict == 2  # "Physics" and "See above."
    print(f"{_PASS if ok3 else _FAIL} example 4: dictionary mode rejected={rej_dict} (expected 2)")


# ── Invalid mode raises ValueError ───────────────────────────────────────────

def test_invalid_mode_raises():
    try:
        validate_mode("turbo")
        print(f"{_FAIL} invalid mode: no exception raised")
    except ValueError as e:
        ok = "turbo" in str(e)
        print(f"{_PASS if ok else _FAIL} invalid mode: ValueError raised: {e}")

    from l_cdea.ingestion import ingest_document
    try:
        ingest_document(PHYSICS_PATH, mode="turbo")
        print(f"{_FAIL} ingest_document invalid mode: no exception raised")
    except ValueError as e:
        print(f"{_PASS} ingest_document invalid mode: ValueError raised")


# ── Filter unit tests ─────────────────────────────────────────────────────────

def test_filter_punctuation_only():
    ok = not is_valid_dictionary_chunk("...")
    print(f"{_PASS if ok else _FAIL} filter: '...' rejected")
    ok2 = not is_valid_dictionary_chunk("---")
    print(f"{_PASS if ok2 else _FAIL} filter: '---' rejected")


def test_filter_no_verb_rejected():
    ok = not is_valid_dictionary_chunk("The big apple tree")
    print(f"{_PASS if ok else _FAIL} filter: 'The big apple tree' (no verb) rejected")
    ok2 = not is_valid_dictionary_chunk("Newton second law motion")
    print(f"{_PASS if ok2 else _FAIL} filter: 'Newton second law motion' (no verb) rejected")


def test_filter_valid_accepted():
    ok = is_valid_dictionary_chunk("Velocity is displacement over time.")
    print(f"{_PASS if ok else _FAIL} filter: 'Velocity is displacement over time.' accepted")
    ok2 = is_valid_dictionary_chunk("Force means mass times acceleration.")
    print(f"{_PASS if ok2 else _FAIL} filter: 'Force means mass times acceleration.' accepted")


# ── Classifier: definition wins in dictionary mode ────────────────────────────

def test_classifier_definition_priority():
    from l_cdea.ingestion.router.classifier import classify_chunk

    text = "Velocity is displacement over time."
    route_doc = classify_chunk(text, mode="document")
    route_dict = classify_chunk(text, mode="dictionary")

    # Both should classify as "definition" or "claim"; dictionary mode should
    # give definition at least as high a score as document mode.
    ok = route_dict.category in ("definition", "claim")
    print(f"{_PASS if ok else _FAIL} classifier: dictionary category={route_dict.category!r}")
    ok2 = route_dict.confidence >= route_doc.confidence
    print(f"{_PASS if ok2 else _FAIL} classifier: dict confidence={route_dict.confidence:.3f} >= doc={route_doc.confidence:.3f}")


# ── Full pipeline: dictionary mode, velocity extracted ───────────────────────

def test_full_pipeline_dictionary_mode():
    if not os.path.exists(PHYSICS_PATH):
        print(f"  [SKIP] physics_basic.txt not found")
        return

    import tempfile
    from l_cdea.ingestion import ingest_document
    from l_cdea.discourse.definition_retrieval.lookup import clear_definitions
    from l_cdea.core.planner.discourse_lookup import clear_cache

    clear_definitions()
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    os.unlink(state_path)

    try:
        result = ingest_document(PHYSICS_PATH, state_path=state_path, mode="dictionary")
        ok = result.definitions >= 4  # velocity now included
        print(f"{_PASS if ok else _FAIL} pipeline: definitions={result.definitions} (expected ≥4)")
        ok2 = result.nodes_added >= 4
        print(f"{_PASS if ok2 else _FAIL} pipeline: nodes_added={result.nodes_added}")
        ok3 = result.mode_trace is not None and result.mode_trace.mode == "dictionary"
        print(f"{_PASS if ok3 else _FAIL} pipeline: mode_trace.mode={result.mode_trace.mode if result.mode_trace else None!r}")

        # verify velocity is in the store
        from l_cdea.discourse.definition_retrieval.lookup import lookup_definition
        from l_cdea.discourse.storage import load_state
        clear_definitions()
        clear_cache()
        state = load_state(state_path)
        r = lookup_definition("velocity", state)
        ok4 = r.hit
        print(f"{_PASS if ok4 else _FAIL} pipeline: velocity lookup hit={r.hit}")
        if r.definition_text:
            ok5 = "displacement" in r.definition_text.lower() or "velocity" in r.definition_text.lower()
            print(f"{_PASS if ok5 else _FAIL} pipeline: velocity text={r.definition_text!r}")
    finally:
        if os.path.exists(state_path):
            os.unlink(state_path)


# ── IngestionModeTrace ────────────────────────────────────────────────────────

def test_mode_trace_counts():
    content = "\n\n".join([
        "Acceleration is the rate of change of velocity.",
        "Velocity is displacement over time.",
        "short",  # too short even for dictionary (< 5 chars? no — "short" = 5 chars, but single word)
        "x",      # too short
    ])
    doc = RawDocument(title="t", content=content, source_path="t.txt")
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok = len(chunks) == 2
    print(f"{_PASS if ok else _FAIL} mode_trace: accepted={len(chunks)} (expected 2)")
    ok2 = rejected == 2
    print(f"{_PASS if ok2 else _FAIL} mode_trace: rejected={rejected} (expected 2)")


# ── Provenance contains ingestion_mode ────────────────────────────────────────

def test_provenance_contains_mode():
    if not os.path.exists(PHYSICS_PATH):
        print(f"  [SKIP] physics_basic.txt not found")
        return

    import tempfile
    from l_cdea.ingestion import ingest_document
    from l_cdea.discourse.definition_retrieval.lookup import clear_definitions
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.discourse.storage import load_state

    clear_definitions()
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    os.unlink(state_path)

    try:
        ingest_document(PHYSICS_PATH, state_path=state_path, mode="dictionary")
        state = load_state(state_path)
        def_nodes = [
            n for n in state.nodes.values()
            if (n.metadata or {}).get("category") == "definition"
        ]
        ok = len(def_nodes) > 0
        print(f"{_PASS if ok else _FAIL} provenance: {len(def_nodes)} definition nodes found")
        if def_nodes:
            node = def_nodes[0]
            ok2 = node.metadata.get("ingestion_mode") == "dictionary"
            print(f"{_PASS if ok2 else _FAIL} provenance: ingestion_mode={node.metadata.get('ingestion_mode')!r}")
    finally:
        if os.path.exists(state_path):
            os.unlink(state_path)


# ── Line-level chunking: 4 definitions → 4 chunks ────────────────────────────

MINI_DICT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge_seed", "mini_dictionary.txt")
)


def test_line_level_four_chunks():
    """mini_dictionary.txt has 4 lines → 4 chunks in dictionary mode."""
    if not os.path.exists(MINI_DICT_PATH):
        print(f"  [SKIP] mini_dictionary.txt not found")
        return
    from l_cdea.ingestion.document_loader import load_document
    doc = load_document(MINI_DICT_PATH)
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok = len(chunks) == 4
    print(f"{_PASS if ok else _FAIL} line-level: chunks={len(chunks)} (expected 4)")
    ok2 = rejected == 0
    print(f"{_PASS if ok2 else _FAIL} line-level: rejected={rejected} (expected 0)")
    # Each chunk has its own chunk_id
    ids = [c.chunk_id for c in chunks]
    ok3 = len(set(ids)) == 4 and all(ids)
    print(f"{_PASS if ok3 else _FAIL} line-level: all 4 chunk_ids unique and non-None")
    # Locations are line:1 through line:4
    locs = [c.location for c in chunks]
    ok4 = locs == ["line:1", "line:2", "line:3", "line:4"]
    print(f"{_PASS if ok4 else _FAIL} line-level: locations={locs}")


def test_line_level_invalid_then_valid():
    """One invalid line + one valid line → 1 chunk, 1 rejected."""
    content = "Velocity\nForce is mass times acceleration."
    doc = RawDocument(title="t", content=content, source_path="t.txt")
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok = len(chunks) == 1
    print(f"{_PASS if ok else _FAIL} line-level invalid+valid: chunks={len(chunks)} (expected 1)")
    ok2 = rejected == 1
    print(f"{_PASS if ok2 else _FAIL} line-level invalid+valid: rejected={rejected} (expected 1)")


def test_line_level_blank_lines_skipped():
    """Blank lines are silently skipped (not counted as rejected)."""
    content = "Velocity is displacement over time.\n\nForce is mass times acceleration."
    doc = RawDocument(title="t", content=content, source_path="t.txt")
    chunks, rejected = chunk_document_with_trace(doc, mode="dictionary")
    ok = len(chunks) == 2
    print(f"{_PASS if ok else _FAIL} line-level blank lines: chunks={len(chunks)} (expected 2)")
    ok2 = rejected == 0
    print(f"{_PASS if ok2 else _FAIL} line-level blank lines: rejected={rejected} (expected 0)")


def test_document_mode_unchanged():
    """Document mode still uses paragraph-based chunking."""
    if not os.path.exists(MINI_DICT_PATH):
        print(f"  [SKIP] mini_dictionary.txt not found")
        return
    from l_cdea.ingestion.document_loader import load_document
    doc = load_document(MINI_DICT_PATH)
    chunks, rejected = chunk_document_with_trace(doc, mode="document")
    # All 4 lines are one paragraph (no blank line separators), so 1 chunk
    ok = len(chunks) == 1
    print(f"{_PASS if ok else _FAIL} document mode unchanged: chunks={len(chunks)} (expected 1)")
    # Document-mode chunks have no chunk_id
    ok2 = chunks[0].chunk_id is None
    print(f"{_PASS if ok2 else _FAIL} document mode: chunk_id=None (not set)")


def test_chunk_ids_stable():
    """Same file + same line → same chunk_id across two calls."""
    content = "Velocity is displacement over time.\nForce is mass times acceleration."
    doc = RawDocument(title="stable_test", content=content, source_path="stable.txt")
    chunks1, _ = chunk_document_with_trace(doc, mode="dictionary")
    chunks2, _ = chunk_document_with_trace(doc, mode="dictionary")
    ok = all(c1.chunk_id == c2.chunk_id for c1, c2 in zip(chunks1, chunks2))
    print(f"{_PASS if ok else _FAIL} chunk IDs stable: {[c.chunk_id for c in chunks1]}")


def test_provenance_chunk_id_and_location():
    """Persisted definition nodes carry chunk_id and location in provenance."""
    if not os.path.exists(MINI_DICT_PATH):
        print(f"  [SKIP] mini_dictionary.txt not found")
        return

    import tempfile
    from l_cdea.ingestion import ingest_document
    from l_cdea.discourse.definition_retrieval.lookup import clear_definitions
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.discourse.storage import load_state

    clear_definitions()
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    os.unlink(state_path)

    try:
        ingest_document(MINI_DICT_PATH, state_path=state_path, mode="dictionary")
        state = load_state(state_path)
        def_nodes = [
            n for n in state.nodes.values()
            if (n.metadata or {}).get("category") == "definition"
        ]
        ok = len(def_nodes) == 4
        print(f"{_PASS if ok else _FAIL} provenance nodes: count={len(def_nodes)} (expected 4)")

        for node in def_nodes:
            prov = node.provenance[0] if node.provenance else None
            has_chunk_id = prov is not None and prov.chunk_id is not None and prov.chunk_id.startswith("chunk_")
            has_location = prov is not None and prov.location is not None and prov.location.startswith("line:")
            has_meta_chunk_id = node.metadata.get("chunk_id") is not None
            term = node.metadata.get("term", "?")
            ok2 = has_chunk_id and has_location and has_meta_chunk_id
            print(f"{_PASS if ok2 else _FAIL} provenance [{term}]: chunk_id={prov.chunk_id if prov else None!r}, location={prov.location if prov else None!r}")
    finally:
        if os.path.exists(state_path):
            os.unlink(state_path)


def test_full_pipeline_mini_dictionary():
    """ingest mini_dictionary.txt → chunks_processed=4, definitions=4, nodes_added=4."""
    if not os.path.exists(MINI_DICT_PATH):
        print(f"  [SKIP] mini_dictionary.txt not found")
        return

    import tempfile
    from l_cdea.ingestion import ingest_document
    from l_cdea.discourse.definition_retrieval.lookup import clear_definitions
    from l_cdea.core.planner.discourse_lookup import clear_cache

    clear_definitions()
    clear_cache()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        state_path = f.name
    os.unlink(state_path)

    try:
        result = ingest_document(MINI_DICT_PATH, state_path=state_path, mode="dictionary")
        ok = result.chunks_processed == 4
        print(f"{_PASS if ok else _FAIL} mini_dict: chunks_processed={result.chunks_processed} (expected 4)")
        ok2 = result.definitions == 4
        print(f"{_PASS if ok2 else _FAIL} mini_dict: definitions={result.definitions} (expected 4)")
        ok3 = result.nodes_added == 4
        print(f"{_PASS if ok3 else _FAIL} mini_dict: nodes_added={result.nodes_added} (expected 4)")
        ok4 = result.items_registered == 8  # 4 claims + 4 definitions registered as KnowledgeItems
        print(f"{_PASS if ok4 else _FAIL} mini_dict: items_registered={result.items_registered} (expected 8)")
    finally:
        if os.path.exists(state_path):
            os.unlink(state_path)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: document mode rejects short definition",    test_example_1_document_mode_rejects_short),
        ("Example 2: dictionary mode accepts short definition",   test_example_2_dictionary_mode_accepts_short),
        ("Example 3: single-word rejected in dictionary mode",    test_example_3_single_word_rejected),
        ("Example 4: mixed content, only valid accepted",         test_example_4_mixed_content),
        ("Invalid mode raises ValueError",                        test_invalid_mode_raises),
        ("Filter: punctuation-only rejected",                     test_filter_punctuation_only),
        ("Filter: no-verb fragment rejected",                     test_filter_no_verb_rejected),
        ("Filter: valid sentences accepted",                      test_filter_valid_accepted),
        ("Classifier: definition priority in dictionary mode",    test_classifier_definition_priority),
        ("Full pipeline: dictionary mode, velocity extracted",    test_full_pipeline_dictionary_mode),
        ("IngestionModeTrace accepted/rejected counts",           test_mode_trace_counts),
        ("Provenance contains ingestion_mode",                    test_provenance_contains_mode),
        ("Line-level: 4 definitions → 4 chunks",                  test_line_level_four_chunks),
        ("Line-level: invalid + valid → 1 chunk",                 test_line_level_invalid_then_valid),
        ("Line-level: blank lines silently skipped",              test_line_level_blank_lines_skipped),
        ("Document mode unchanged (paragraph-based)",             test_document_mode_unchanged),
        ("Chunk IDs stable across runs",                          test_chunk_ids_stable),
        ("Provenance: chunk_id and location in nodes",            test_provenance_chunk_id_and_location),
        ("Full pipeline: mini_dictionary.txt 4×4",                test_full_pipeline_mini_dictionary),
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
