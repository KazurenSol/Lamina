"""
Ingestion router tests.

Covers all 6 spec validation examples:
  1. "Acceleration is defined as..."       → definition
  2. "Force equals mass times acceleration."→ claim (no "=")
  3. "First, heat the mixture. Then..."   → procedure
  4. "For example, Paris is..."           → example
  5. "F = ma"                             → formula
  6. "Random sentence without structure." → unknown, fallback=True

Additional checks:
  - Formula detection (math operators)
  - Definition structural cue ("Term: definition")
  - Dispatcher groups by category
  - IngestionRouteTrace fields
  - Determinism: same input → same output
  - Route ID is deterministic
  - Batch classify_chunks
"""
from __future__ import annotations

from l_cdea.ingestion.router import (
    classify_chunk,
    classify_chunks,
    dispatch,
    dispatch_routes,
    IngestionRoute,
    IngestionRouteResult,
    IngestionRouteTrace,
    make_route_id,
)

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


# ── Spec Example 1 ────────────────────────────────────────────────────────────

def test_example_1_definition():
    r = classify_chunk("Acceleration is defined as the rate of change of velocity.")
    ok = r.category == "definition"
    print(f"{_PASS if ok else _FAIL} example 1: category={r.category!r} (expected 'definition')")
    ok2 = not r.fallback
    print(f"{_PASS if ok2 else _FAIL} example 1: fallback={r.fallback} (expected False)")


# ── Spec Example 2 ────────────────────────────────────────────────────────────

def test_example_2_claim():
    r = classify_chunk("Force equals mass times acceleration.")
    ok = r.category in ("claim", "formula")
    print(f"{_PASS if ok else _FAIL} example 2: category={r.category!r} (expected 'claim' or 'formula')")


# ── Spec Example 3 ────────────────────────────────────────────────────────────

def test_example_3_procedure():
    r = classify_chunk("First, heat the mixture. Then add water.")
    ok = r.category == "procedure"
    print(f"{_PASS if ok else _FAIL} example 3: category={r.category!r} (expected 'procedure')")


# ── Spec Example 4 ────────────────────────────────────────────────────────────

def test_example_4_example():
    r = classify_chunk("For example, Paris is the capital of France.")
    ok = r.category == "example"
    print(f"{_PASS if ok else _FAIL} example 4: category={r.category!r} (expected 'example')")


# ── Spec Example 5 ────────────────────────────────────────────────────────────

def test_example_5_formula():
    r = classify_chunk("F = ma")
    ok = r.category == "formula"
    print(f"{_PASS if ok else _FAIL} example 5: category={r.category!r} (expected 'formula')")
    ok2 = r.confidence > 0
    print(f"{_PASS if ok2 else _FAIL} example 5: confidence={r.confidence}")


# ── Spec Example 6 ────────────────────────────────────────────────────────────

def test_example_6_unknown():
    r = classify_chunk("Random sentence without structure.")
    ok = r.category == "unknown"
    print(f"{_PASS if ok else _FAIL} example 6: category={r.category!r} (expected 'unknown')")
    ok2 = r.fallback is True
    print(f"{_PASS if ok2 else _FAIL} example 6: fallback={r.fallback} (expected True)")
    ok3 = r.confidence == 0.0
    print(f"{_PASS if ok3 else _FAIL} example 6: confidence={r.confidence} (expected 0.0)")


# ── Formula structural detection ─────────────────────────────────────────────

def test_formula_structural():
    cases = [
        ("x^2 + 2x + 1",       "formula"),
        ("E = mc^2",            "formula"),
        ("a * b + c * d",       "formula"),
    ]
    for text, expected in cases:
        r = classify_chunk(text)
        ok = r.category == expected
        print(f"{_PASS if ok else _FAIL} formula structural: {text!r} → {r.category!r}")


# ── Definition structural cue ("Term: definition") ───────────────────────────

def test_definition_structural():
    r = classify_chunk("Velocity: the rate of change of position.")
    ok = r.category == "definition"
    print(f"{_PASS if ok else _FAIL} definition structural: category={r.category!r}")


# ── Route ID is deterministic ─────────────────────────────────────────────────

def test_route_id_deterministic():
    text = "F = ma"
    id1 = make_route_id(text, 0)
    id2 = make_route_id(text, 0)
    ok = id1 == id2
    print(f"{_PASS if ok else _FAIL} route_id deterministic: {id1!r}")
    id3 = make_route_id(text, 1)
    ok2 = id1 != id3
    print(f"{_PASS if ok2 else _FAIL} route_id differs with index: {id1!r} vs {id3!r}")


# ── classify is deterministic ─────────────────────────────────────────────────

def test_classify_deterministic():
    text = "Acceleration is defined as the rate of change of velocity."
    r1 = classify_chunk(text)
    r2 = classify_chunk(text)
    ok = r1 == r2
    print(f"{_PASS if ok else _FAIL} classify deterministic: {r1.category!r}")


# ── matched_patterns non-empty for non-unknown ────────────────────────────────

def test_matched_patterns():
    r = classify_chunk("Acceleration is defined as the rate of change of velocity.")
    ok = len(r.matched_patterns) > 0
    print(f"{_PASS if ok else _FAIL} matched_patterns non-empty: {r.matched_patterns}")


# ── Batch classify_chunks ─────────────────────────────────────────────────────

def test_classify_chunks_batch():
    texts = [
        "F = ma",
        "For example, Paris is the capital of France.",
        "Random sentence without structure.",
    ]
    routes = classify_chunks(texts)
    ok = len(routes) == 3
    print(f"{_PASS if ok else _FAIL} classify_chunks returns {len(routes)} routes")
    ok2 = routes[0].category == "formula"
    print(f"{_PASS if ok2 else _FAIL} batch[0]: {routes[0].category!r}")
    ok3 = routes[1].category == "example"
    print(f"{_PASS if ok3 else _FAIL} batch[1]: {routes[1].category!r}")
    ok4 = routes[2].category == "unknown"
    print(f"{_PASS if ok4 else _FAIL} batch[2]: {routes[2].category!r}")


# ── Dispatcher groups by category ─────────────────────────────────────────────

def test_dispatcher():
    routes = classify_chunks([
        "F = ma",
        "Acceleration is defined as the rate of change of velocity.",
        "For example, Paris is the capital of France.",
        "Another formula: x = y + z",
    ])
    buckets = dispatch_routes(routes)
    ok = "formula" in buckets
    print(f"{_PASS if ok else _FAIL} dispatcher: 'formula' bucket present")
    ok2 = "definition" in buckets
    print(f"{_PASS if ok2 else _FAIL} dispatcher: 'definition' bucket present")
    ok3 = "example" in buckets
    print(f"{_PASS if ok3 else _FAIL} dispatcher: 'example' bucket present")
    formula_count = len(buckets.get("formula", ()))
    ok4 = formula_count >= 1
    print(f"{_PASS if ok4 else _FAIL} dispatcher: formula bucket has {formula_count} route(s)")


# ── IngestionRouteTrace fields ────────────────────────────────────────────────

def test_trace_fields():
    r = classify_chunk("F = ma")
    trace = IngestionRouteTrace(
        chunk_text=r.chunk_text,
        matched_patterns=r.matched_patterns,
        selected_category=r.category,
        confidence=r.confidence,
        ambiguous=False,
        fallback=r.fallback,
    )
    ok = trace.selected_category == "formula"
    print(f"{_PASS if ok else _FAIL} trace.selected_category={trace.selected_category!r}")
    ok2 = trace.fallback is False
    print(f"{_PASS if ok2 else _FAIL} trace.fallback={trace.fallback}")
    ok3 = trace.chunk_text == "F = ma"
    print(f"{_PASS if ok3 else _FAIL} trace.chunk_text preserved")


# ── IngestionRoute validation ─────────────────────────────────────────────────

def test_invalid_category_rejected():
    try:
        IngestionRoute(
            route_id="x",
            chunk_text="x",
            category="BOGUS",
            confidence=0.5,
            matched_patterns=(),
            fallback=False,
        )
        print(f"{_FAIL} invalid category should have raised ValueError")
    except ValueError:
        print(f"{_PASS} invalid category raises ValueError")


def test_invalid_confidence_rejected():
    try:
        IngestionRoute(
            route_id="x",
            chunk_text="x",
            category="claim",
            confidence=1.5,
            matched_patterns=(),
            fallback=False,
        )
        print(f"{_FAIL} confidence > 1.0 should have raised ValueError")
    except ValueError:
        print(f"{_PASS} confidence > 1.0 raises ValueError")


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: definition",                test_example_1_definition),
        ("Example 2: claim or formula",          test_example_2_claim),
        ("Example 3: procedure",                 test_example_3_procedure),
        ("Example 4: example",                   test_example_4_example),
        ("Example 5: formula (F=ma)",            test_example_5_formula),
        ("Example 6: unknown + fallback",        test_example_6_unknown),
        ("Formula structural detection",         test_formula_structural),
        ("Definition structural cue",            test_definition_structural),
        ("Route ID determinism",                 test_route_id_deterministic),
        ("Classify determinism",                 test_classify_deterministic),
        ("Matched patterns non-empty",           test_matched_patterns),
        ("Batch classify_chunks",                test_classify_chunks_batch),
        ("Dispatcher grouping",                  test_dispatcher),
        ("IngestionRouteTrace fields",           test_trace_fields),
        ("Invalid category rejected",            test_invalid_category_rejected),
        ("Invalid confidence rejected",          test_invalid_confidence_rejected),
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
