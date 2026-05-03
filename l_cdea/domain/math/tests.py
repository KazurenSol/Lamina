def test_math_operators():
    import l_cdea.domain.math
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.math.operators import ADD, SUBTRACT, MULTIPLY, DIVIDE, SOLVE, IS_EQUAL, CONTAINS

    assert "math.ADD" in OperatorRegistry.list()
    assert "math.SOLVE" in OperatorRegistry.list()
    assert "math.CONTAINS" in OperatorRegistry.list()

    E, P, C = SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.CONSTRAINT

    result = ADD.execute(TypedValue(3, E), TypedValue(5, E))
    assert result.value == 8

    result2 = SUBTRACT.execute(TypedValue(10, E), TypedValue(4, E))
    assert result2.value == 6

    result3 = MULTIPLY.execute(TypedValue(3, E), TypedValue(7, E))
    assert result3.value == 21

    result4 = DIVIDE.execute(TypedValue(10, E), TypedValue(2, E))
    assert result4.value == 5.0

    result5 = IS_EQUAL.execute(TypedValue(3, E), TypedValue(3, E))
    assert result5.value is True

    result6 = IS_EQUAL.execute(TypedValue(3, E), TypedValue(4, E))
    assert result6.value is False

    collection = TypedValue([1, 2, 3], E)
    result7 = CONTAINS.execute(collection, TypedValue(2, E))
    assert result7.value is True

    print("Math tests PASSED")


if __name__ == "__main__":
    test_math_operators()
