def test_geography_operators():
    import l_cdea.data  # ensures datasets are registered
    import l_cdea.domain.geography  # triggers operator registration
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.geography.operators import LOCATED_IN, CAPITAL_OF, GEO_LOOKUP

    assert "geography.LOCATED_IN" in OperatorRegistry.list()
    assert "geography.CAPITAL_OF" in OperatorRegistry.list()

    result = LOCATED_IN.execute(
        TypedValue("Paris", SemanticType.ENTITY),
        TypedValue("France", SemanticType.ENTITY),
    )
    assert result.type == SemanticType.RELATION
    assert "Paris" in str(result.value)

    mapping = {"Texas": "Austin", "California": "Sacramento"}
    result2 = GEO_LOOKUP.execute(
        TypedValue("Texas", SemanticType.ENTITY),
        TypedValue(mapping, SemanticType.ENTITY),
    )
    assert result2.value == "Austin"

    # Data-backed CAPITAL_OF — now returns real values
    result3 = CAPITAL_OF.execute(TypedValue("France", SemanticType.ENTITY))
    assert result3.value == "Paris", f"Expected Paris, got {result3.value!r}"

    result4 = CAPITAL_OF.execute(TypedValue("Texas", SemanticType.ENTITY))
    assert result4.value == "Austin", f"Expected Austin, got {result4.value!r}"

    # Fallback: unknown region returns symbolic, does not crash
    result5 = CAPITAL_OF.execute(TypedValue("Atlantis", SemanticType.ENTITY))
    assert "Atlantis" in str(result5.value), f"Expected symbolic fallback, got {result5.value!r}"

    print("Geography tests PASSED")


if __name__ == "__main__":
    test_geography_operators()
