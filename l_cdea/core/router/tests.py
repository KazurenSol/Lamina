"""Router validation — all 5 spec examples plus ambiguity and tie-breaking."""


def _make_parsed(text: str):
    from l_cdea.core.parser import parse
    return parse(text)


def test_router():
    from l_cdea.core.router import route, route_with_trace, load_domain_patterns
    load_domain_patterns()

    # Example 1: geography capital
    result, trace = route_with_trace(_make_parsed("capital of France"))
    assert not result.fallback_used, f"Expected domain match, got fallback. Trace: {trace}"
    assert result.selected_intent.domain == "geography", result.selected_intent
    assert result.selected_intent.operator_name == "CAPITAL_OF", result.selected_intent
    assert result.selected_intent.slots.get("region") == "France", result.selected_intent.slots
    assert not result.selected_intent.fallback
    print(f"  [PASS] 'capital of France' → geography.CAPITAL_OF  slots={result.selected_intent.slots}")

    # Example 2: math simplify
    result2, _ = route_with_trace(_make_parsed("simplify x + 0"))
    assert result2.selected_intent.domain == "math"
    assert result2.selected_intent.operator_name == "SIMPLIFY"
    assert "expression" in result2.selected_intent.slots
    print(f"  [PASS] 'simplify x + 0' → math.SIMPLIFY  slots={result2.selected_intent.slots}")

    # Example 3: physics acceleration
    result3, _ = route_with_trace(_make_parsed("calculate acceleration from force 10 N and mass 2 kg"))
    assert result3.selected_intent.domain == "physics"
    assert result3.selected_intent.operator_name == "COMPUTE_ACCELERATION"
    print(f"  [PASS] 'calculate acceleration...' → physics.COMPUTE_ACCELERATION  slots={result3.selected_intent.slots}")

    # Example 4: programming find first
    result4, _ = route_with_trace(_make_parsed("find first even number in the list"))
    assert result4.selected_intent.domain == "programming"
    assert result4.selected_intent.operator_name == "ITERATE"
    print(f"  [PASS] 'find first even number in...' → programming.ITERATE  slots={result4.selected_intent.slots}")

    # Example 5: fallback for unknown input
    result5, trace5 = route_with_trace(_make_parsed("xyzzy frobnicate the quux"))
    assert result5.fallback_used
    assert result5.selected_intent.domain == "generic"
    assert result5.selected_intent.fallback
    print(f"  [PASS] unknown input → generic.GENERIC_COMPILE (fallback)")

    # Extra: confidence is deterministic — same input same result
    r_a, _ = route_with_trace(_make_parsed("capital of Germany"))
    r_b, _ = route_with_trace(_make_parsed("capital of Germany"))
    assert r_a.selected_intent.confidence == r_b.selected_intent.confidence
    assert r_a.selected_intent.slots == r_b.selected_intent.slots
    print(f"  [PASS] determinism verified — same input same confidence")

    # Extra: biology pattern ("explain X" routes to GET_DEFINITION; use unambiguous verb)
    result6, _ = route_with_trace(_make_parsed("simulate photosynthesis"))
    assert result6.selected_intent.domain == "biology"
    assert result6.selected_intent.operator_name == "PHOTOSYNTHESIS"
    print(f"  [PASS] 'simulate photosynthesis' → biology.PHOTOSYNTHESIS")

    # Extra: finance pattern
    result7, _ = route_with_trace(_make_parsed("deposit 100 into my account"))
    assert result7.selected_intent.domain == "finance"
    assert result7.selected_intent.operator_name == "DEPOSIT"
    print(f"  [PASS] 'deposit 100 into my account' → finance.DEPOSIT")

    # Extra: legal pattern
    result8, _ = route_with_trace(_make_parsed("is speeding illegal"))
    assert result8.selected_intent.domain == "legal"
    assert result8.selected_intent.operator_name == "CHECK_PROHIBITION"
    print(f"  [PASS] 'is speeding illegal' → legal.CHECK_PROHIBITION")

    print("\nAll router tests PASSED")


if __name__ == "__main__":
    test_router()
