def test_programming_operators():
    import l_cdea.domain.programming
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.programming.operators import (
        DEFINE_VARIABLE, ASSIGN, CALL_FUNCTION, LOOKUP_KEY,
        CONDITIONAL_BRANCH, COMPARE_VALUES,
    )

    assert "programming.DEFINE_VARIABLE" in OperatorRegistry.list()
    assert "programming.LOOKUP_KEY" in OperatorRegistry.list()
    assert "programming.CONDITIONAL_BRANCH" in OperatorRegistry.list()

    E, S, C, A = (SemanticType.ENTITY, SemanticType.STATE,
                  SemanticType.CONSTRAINT, SemanticType.ABSTRACTION)

    result = DEFINE_VARIABLE.execute(TypedValue("x", A), TypedValue(42, E))
    assert result.type == E
    assert result.value == {"name": "x", "value": 42}

    result2 = LOOKUP_KEY.execute(TypedValue({"Texas": "Austin"}, E), TypedValue("Texas", E))
    assert result2.value == "Austin"

    result3 = COMPARE_VALUES.execute(TypedValue(5, E), TypedValue(10, E), TypedValue("lt", A))
    assert result3.type == C

    print("Programming tests PASSED")


if __name__ == "__main__":
    test_programming_operators()
