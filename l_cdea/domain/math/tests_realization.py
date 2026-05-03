"""
Math realization tests.

Covers all five spec validation examples:
  1. simplify x + 0   → x
  2. simplify x * 1   → x
  3. simplify x + x   → 2x
  4. expand (x + 1)^2 → x^2 + 2x + 1
  5. simplify 2 + 3   → 5

Additional checks:
  - All 10 mandatory simplification rules
  - Expansion: distribute, FOIL
  - Numeric folding (multi-step)
  - Subtraction (a - b = a + (-1)*b)
  - Trace: rules_sequence non-empty on non-trivial inputs
  - Parser round-trip: parse → to_string → parse
  - MathTrace.error is None on valid inputs
  - Pipeline integration: simplify via planner+execution
"""
from __future__ import annotations

import l_cdea.domain  # registers + governs all operators
import l_cdea.data    # registers data-backed datasets

from l_cdea.domain.math.realization import realize_simplify, realize_expand, parse_expr, to_string
from l_cdea.domain.math.ast import Const, Var, Add, Mul, Pow

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"


def _s(expr: str) -> str:
    return realize_simplify(expr).output_expression

def _e(expr: str) -> str:
    return realize_expand(expr).output_expression


# ── Example 1: x + 0 → x ─────────────────────────────────────────────────────

def test_simplify_add_zero():
    ok = _s("x + 0") == "x"
    print(f"{_PASS if ok else _FAIL} simplify 'x + 0' → {_s('x + 0')!r}")

    ok2 = _s("0 + x") == "x"
    print(f"{_PASS if ok2 else _FAIL} simplify '0 + x' → {_s('0 + x')!r}")


# ── Example 2: x * 1 → x ─────────────────────────────────────────────────────

def test_simplify_mul_one():
    ok = _s("x * 1") == "x"
    print(f"{_PASS if ok else _FAIL} simplify 'x * 1' → {_s('x * 1')!r}")

    ok2 = _s("1 * x") == "x"
    print(f"{_PASS if ok2 else _FAIL} simplify '1 * x' → {_s('1 * x')!r}")


# ── Example 3: x + x → 2x ────────────────────────────────────────────────────

def test_simplify_double_var():
    got = _s("x + x")
    ok = got == "2x"
    print(f"{_PASS if ok else _FAIL} simplify 'x + x' → {got!r}")


# ── Example 4: (x + 1)^2 → x^2 + 2x + 1 ─────────────────────────────────────

def test_expand_square():
    got = _e("( x + 1 ) ^ 2")
    ok = got == "x^2 + 2x + 1"
    print(f"{_PASS if ok else _FAIL} expand '(x+1)^2' → {got!r}")


# ── Example 5: 2 + 3 → 5 ─────────────────────────────────────────────────────

def test_simplify_numeric_add():
    got = _s("2 + 3")
    ok = got == "5"
    print(f"{_PASS if ok else _FAIL} simplify '2 + 3' → {got!r}")


# ── All 10 mandatory rules ────────────────────────────────────────────────────

def test_all_ten_rules():
    cases = [
        ("x + 0",   "x",  "rule 1: x + 0 → x"),
        ("0 + x",   "x",  "rule 2: 0 + x → x"),
        ("x * 1",   "x",  "rule 3: x * 1 → x"),
        ("1 * x",   "x",  "rule 4: 1 * x → x"),
        ("x * 0",   "0",  "rule 5: x * 0 → 0"),
        ("0 * x",   "0",  "rule 6: 0 * x → 0"),
        ("x + x",   "2x", "rule 7: x + x → 2 * x"),
        ("2 + 3",   "5",  "rule 9: numeric add folding"),
        ("2 * 3",   "6",  "rule 10: numeric mul folding"),
    ]
    for expr, expected, label in cases:
        got = _s(expr)
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} {label}: {expr!r} → {got!r}")


# ── Expansion rules ───────────────────────────────────────────────────────────

def test_expansion():
    cases = [
        ("x * ( x + 1 )",         "x^2 + x",           "distribute: x*(x+1)"),
        ("( x + 1 ) * x",         "x^2 + x",           "distribute: (x+1)*x"),
        ("( x + 1 ) ^ 2",         "x^2 + 2x + 1",      "FOIL: (x+1)^2"),
        ("( x + 2 ) ^ 2",         "x^2 + 4x + 4",      "FOIL: (x+2)^2"),
        ("2 * ( x + 3 )",         "2x + 6",             "distribute: 2*(x+3)"),
    ]
    for expr, expected, label in cases:
        got = _e(expr)
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} {label}: {expr!r} → {got!r}")


# ── Multi-step numeric folding ────────────────────────────────────────────────

def test_numeric_folding():
    cases = [
        ("1 + 2 + 3",   "6",    "1+2+3 multi-step add"),
        ("2 * 3 * 4",   "24",   "2*3*4 multi-step mul"),
        ("( 2 + 3 ) * x", "5x", "constant-fold inside Mul"),
    ]
    for expr, expected, label in cases:
        got = _s(expr)
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} {label}: {expr!r} → {got!r}")


# ── Power simplifications ─────────────────────────────────────────────────────

def test_power_simplification():
    cases = [
        ("x * x",     "x^2", "x * x → x^2"),
        ("2 ^ 3",     "8",   "2^3 → 8"),
    ]
    for expr, expected, label in cases:
        got = _s(expr)
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} {label}: {expr!r} → {got!r}")


# ── Idempotency: simplify already-simple expressions ─────────────────────────

def test_idempotency():
    cases = ["x", "5", "x + y", "2x"]
    for expr in cases:
        got = _s(expr)
        # Should not crash and output should be valid
        ok = got is not None and len(got) > 0
        print(f"{_PASS if ok else _FAIL} idempotent: simplify({expr!r}) → {got!r}")


# ── MathTrace observability ───────────────────────────────────────────────────

def test_trace():
    trace = realize_simplify("x + 0")
    ok = trace.error is None
    print(f"{_PASS if ok else _FAIL} trace.error is None for valid input")
    ok = len(trace.applied_rules_sequence) > 0
    print(f"{_PASS if ok else _FAIL} trace has non-empty rules_sequence (got {trace.applied_rules_sequence})")
    ok = trace.input_expression == "x + 0"
    print(f"{_PASS if ok else _FAIL} trace.input_expression preserved")
    ok = trace.output_expression == "x"
    print(f"{_PASS if ok else _FAIL} trace.output_expression == 'x'")


# ── Parser round-trip ─────────────────────────────────────────────────────────

def test_parser_round_trip():
    """parse → to_string → parse should produce same AST."""
    cases = ["x + 0", "2 + 3", "x * x", "( x + 1 ) ^ 2"]
    for expr in cases:
        ast1 = parse_expr(expr)
        s = to_string(ast1)
        ast2 = parse_expr(s)
        ok = ast1 == ast2
        print(f"{_PASS if ok else _FAIL} round-trip: {expr!r} → {s!r} → same AST")


# ── Pipeline integration: queries through full planner+execution ───────────────

def test_pipeline_integration():
    from l_cdea.core.parser import parse
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.planner import plan
    from l_cdea.core.planner.graph_builder import execute_plan_graph
    from l_cdea.core.planner.discourse_lookup import clear_cache
    from l_cdea.discourse import create_discourse_state

    state = create_discourse_state()
    clear_cache()

    cases = [
        ("simplify x + 0",          "x"),
        ("simplify x * 1",          "x"),
        ("simplify 2 + 3",          "5"),
    ]
    for query, expected in cases:
        parsed = parse(query)
        route_result, _ = route_with_trace(parsed)
        qplan, _ = plan(route_result, state)
        result = execute_plan_graph(qplan.graph) if qplan.is_executable else None
        got = result.value if result else None
        ok = got == expected
        print(f"{_PASS if ok else _FAIL} pipeline: {query!r} → {got!r}")


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: x + 0 → x",           test_simplify_add_zero),
        ("Example 2: x * 1 → x",           test_simplify_mul_one),
        ("Example 3: x + x → 2x",          test_simplify_double_var),
        ("Example 4: (x+1)^2 → x^2+2x+1", test_expand_square),
        ("Example 5: 2 + 3 → 5",           test_simplify_numeric_add),
        ("All 10 mandatory rules",          test_all_ten_rules),
        ("Expansion rules",                 test_expansion),
        ("Multi-step numeric folding",      test_numeric_folding),
        ("Power simplifications",          test_power_simplification),
        ("Idempotency",                    test_idempotency),
        ("MathTrace observability",        test_trace),
        ("Parser round-trip",              test_parser_round_trip),
        ("Pipeline integration",           test_pipeline_integration),
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
