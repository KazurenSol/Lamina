"""
Tests for l_cdea.core.router.paraphrase_patterns

Covers all six spec validation examples plus normalization, false-positive
prevention, and each new pattern group.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../.."))


# ── normalization ─────────────────────────────────────────────────────────────

def test_normalize_can_you():
    from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query
    assert normalize_query("Can you explain force?") == "explain force"
    print("  [PASS] normalize_can_you")


def test_normalize_show_me():
    from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query
    assert normalize_query("show me dependency chain for velocity") == "dependency chain for velocity"
    print("  [PASS] normalize_show_me")


def test_normalize_tell_me():
    from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query
    assert normalize_query("tell me about acceleration") == "about acceleration"
    print("  [PASS] normalize_tell_me")


def test_normalize_could_you():
    from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query
    assert normalize_query("could you define force") == "define force"
    print("  [PASS] normalize_could_you")


def test_normalize_plain():
    from l_cdea.core.router.paraphrase_patterns.normalization import normalize_query
    assert normalize_query("what is force") == "what is force"
    print("  [PASS] normalize_plain")


# ── spec validation examples ──────────────────────────────────────────────────

def test_example1_explain_force():
    """Example 1: 'explain force' → GET_DEFINITION."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("explain force"))
    assert result.selected_intent.operator_name == "GET_DEFINITION", \
        f"got {result.selected_intent.operator_name}"
    assert result.selected_intent.slots.get("term") == "force"
    print("  [PASS] example1_explain_force")


def test_example2_what_affects_force():
    """Example 2: 'what affects force' → GET_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what affects force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    assert intent.slots.get("relation_type") == "depends_on"
    print("  [PASS] example2_what_affects_force")


def test_example3_show_dependency_chain():
    """Example 3: 'show dependency chain for force' → GET_RELATIONSHIP_CLOSURE."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("show dependency chain for force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] example3_show_dependency_chain")


def test_example4_what_indirectly_affects():
    """Example 4: 'what indirectly affects force' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what indirectly affects force"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] example4_what_indirectly_affects")


def test_example5_tell_me_about():
    """Example 5: 'tell me about velocity' → GET_DEFINITION."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("tell me about velocity"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_DEFINITION", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "velocity"
    print("  [PASS] example5_tell_me_about")


def test_example6_random_text():
    """Example 6: 'random unrelated text' → generic fallback."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("random unrelated text"))
    assert result.fallback_used, f"expected fallback, got {result.selected_intent.operator_name}"
    print("  [PASS] example6_random_fallback")


# ── definition paraphrases ────────────────────────────────────────────────────

def test_def_what_is_about():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what is force about"))
    assert result.selected_intent.operator_name == "GET_DEFINITION"
    assert result.selected_intent.slots.get("term") == "force"
    print("  [PASS] def_what_is_about")


def test_def_give_definition():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("give definition of acceleration"))
    assert result.selected_intent.operator_name == "GET_DEFINITION"
    assert result.selected_intent.slots.get("term") == "acceleration"
    print("  [PASS] def_give_definition")


# ── relationship paraphrases (one-hop) ────────────────────────────────────────

def test_rel_what_influences():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what influences velocity"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "velocity"
    assert intent.slots.get("relation_type") == "depends_on"
    print("  [PASS] rel_what_influences")


def test_rel_based_on():
    """'what is X based on' → GET_RELATIONSHIPS (not definition)."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what is force based on"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] rel_based_on")


def test_rel_what_determines():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what determines acceleration"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "acceleration"
    print("  [PASS] rel_what_determines")


def test_rel_dependencies_of():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("dependencies of force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] rel_dependencies_of")


def test_rel_rely_on():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what does acceleration rely on"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "acceleration"
    print("  [PASS] rel_rely_on")


# ── relationship paraphrases (multi-hop) ──────────────────────────────────────

def test_mh_full_dependencies():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("full dependencies of force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] mh_full_dependencies")


def test_mh_all_dependencies():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("all dependencies of velocity"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "velocity"
    print("  [PASS] mh_all_dependencies")


def test_mh_dependency_graph():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("dependency graph for force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_RELATIONSHIP_CLOSURE", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] mh_dependency_graph")


# ── composition paraphrases ───────────────────────────────────────────────────

def test_cr_ultimately_based_on():
    """'what is X ultimately based on' → COMPOSE_RELATIONSHIPS (not definition)."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what is force ultimately based on"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] cr_ultimately_based_on")


def test_cr_derived_dependencies():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("derived dependencies of force"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] cr_derived_dependencies")


def test_cr_indirect_dependencies():
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("indirect dependencies of force"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force"
    print("  [PASS] cr_indirect_dependencies")


# ── false-positive prevention ─────────────────────────────────────────────────

def test_fp_what_is_force_not_relationships():
    """'what is force' MUST NOT map to relationships."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what is force"))
    assert result.selected_intent.operator_name == "GET_DEFINITION", \
        f"got {result.selected_intent.operator_name}"
    print("  [PASS] fp_what_is_force_not_relationships")


def test_fp_what_affects_not_definition():
    """'what affects force' MUST NOT map to definition."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what affects force"))
    assert result.selected_intent.operator_name != "GET_DEFINITION", \
        "incorrectly mapped to definition"
    print("  [PASS] fp_what_affects_not_definition")


def test_fp_ultimately_forces_composition():
    """Presence of 'ultimately' forces composition over definition."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what is force ultimately based on"))
    assert result.selected_intent.operator_name == "COMPOSE_RELATIONSHIPS", \
        f"got {result.selected_intent.operator_name}"
    print("  [PASS] fp_ultimately_forces_composition")


def test_fp_polite_prefix_stripped_in_term():
    """'can you explain force' → term should be 'force', not 'can you force'."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("can you explain force"))
    intent = result.selected_intent
    assert intent.operator_name == "GET_DEFINITION", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force", f"term={intent.slots.get('term')}"
    print("  [PASS] fp_polite_prefix_stripped_in_term")


# ── indirect routing scope ────────────────────────────────────────────────────
# These five cases lock the routing behaviour for "indirect"-containing queries.
# Rules:
#   indirect + dependency marker  → COMPOSE_RELATIONSHIPS
#   "indirect" with no relationship context → generic fallback (never hijacked)

def test_indirect_scope_1_indirectly_depend():
    """'what does force indirectly depend on' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what does force indirectly depend on"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force", f"term={intent.slots.get('term')}"
    print("  [PASS] indirect_scope_1: 'indirectly depend on' → COMPOSE_RELATIONSHIPS")


def test_indirect_scope_2_indirectly_affects():
    """'what indirectly affects force' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("what indirectly affects force"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force", f"term={intent.slots.get('term')}"
    print("  [PASS] indirect_scope_2: 'indirectly affects' → COMPOSE_RELATIONSHIPS")


def test_indirect_scope_3_indirect_dependencies():
    """'indirect dependencies of force' → COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("indirect dependencies of force"))
    intent = result.selected_intent
    assert intent.operator_name == "COMPOSE_RELATIONSHIPS", f"got {intent.operator_name}"
    assert intent.slots.get("term") == "force", f"term={intent.slots.get('term')}"
    print("  [PASS] indirect_scope_3: 'indirect dependencies' → COMPOSE_RELATIONSHIPS")


def test_indirect_scope_4_indirect_lighting():
    """'indirect lighting' — no relationship context → NOT COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("indirect lighting"))
    assert result.selected_intent.operator_name != "COMPOSE_RELATIONSHIPS", \
        f"incorrectly routed to COMPOSE_RELATIONSHIPS"
    print(f"  [PASS] indirect_scope_4: 'indirect lighting' → {result.selected_intent.operator_name}")


def test_indirect_scope_5_indirect_tax():
    """'indirect tax' — no relationship context → NOT COMPOSE_RELATIONSHIPS."""
    from l_cdea.core.router import route_with_trace
    from l_cdea.core.parser import parse
    result, _ = route_with_trace(parse("indirect tax"))
    assert result.selected_intent.operator_name != "COMPOSE_RELATIONSHIPS", \
        f"incorrectly routed to COMPOSE_RELATIONSHIPS"
    print(f"  [PASS] indirect_scope_5: 'indirect tax' → {result.selected_intent.operator_name}")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sections = [
        ("── normalization", [
            test_normalize_can_you,
            test_normalize_show_me,
            test_normalize_tell_me,
            test_normalize_could_you,
            test_normalize_plain,
        ]),
        ("── spec examples", [
            test_example1_explain_force,
            test_example2_what_affects_force,
            test_example3_show_dependency_chain,
            test_example4_what_indirectly_affects,
            test_example5_tell_me_about,
            test_example6_random_text,
        ]),
        ("── definition paraphrases", [
            test_def_what_is_about,
            test_def_give_definition,
        ]),
        ("── one-hop paraphrases", [
            test_rel_what_influences,
            test_rel_based_on,
            test_rel_what_determines,
            test_rel_dependencies_of,
            test_rel_rely_on,
        ]),
        ("── multi-hop paraphrases", [
            test_mh_full_dependencies,
            test_mh_all_dependencies,
            test_mh_dependency_graph,
        ]),
        ("── composition paraphrases", [
            test_cr_ultimately_based_on,
            test_cr_derived_dependencies,
            test_cr_indirect_dependencies,
        ]),
        ("── false-positive prevention", [
            test_fp_what_is_force_not_relationships,
            test_fp_what_affects_not_definition,
            test_fp_ultimately_forces_composition,
            test_fp_polite_prefix_stripped_in_term,
        ]),
        ("── indirect routing scope", [
            test_indirect_scope_1_indirectly_depend,
            test_indirect_scope_2_indirectly_affects,
            test_indirect_scope_3_indirect_dependencies,
            test_indirect_scope_4_indirect_lighting,
            test_indirect_scope_5_indirect_tax,
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
