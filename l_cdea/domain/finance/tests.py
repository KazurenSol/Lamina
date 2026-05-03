def test_finance_operators():
    import l_cdea.domain.finance
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.finance.operators import (
        DEPOSIT, WITHDRAW, TRANSFER, COMPUTE_INTEREST,
        COMPUTE_COMPOUND_INTEREST, COMPARE_VALUES,
    )

    assert "finance.DEPOSIT" in OperatorRegistry.list()
    assert "finance.WITHDRAW" in OperatorRegistry.list()
    assert "finance.COMPUTE_COMPOUND_INTEREST" in OperatorRegistry.list()

    E, S, C = SemanticType.ENTITY, SemanticType.STATE, SemanticType.CONSTRAINT

    acct   = TypedValue("savings", E)
    amount = TypedValue(100, E)
    result = DEPOSIT.execute(acct, amount)
    assert result.type == S
    assert "savings" in str(result.value)

    result2 = WITHDRAW.execute(acct, amount)
    assert "savings" in str(result2.value)

    principal = TypedValue(1000, E)
    rate      = TypedValue(0.05, C)
    time_val  = TypedValue(3, E)
    interest  = COMPUTE_INTEREST.execute(principal, rate, time_val)
    assert interest.value == 150.0

    ci = COMPUTE_COMPOUND_INTEREST.execute(
        TypedValue(1000, E), TypedValue(0.1, C), TypedValue(2, E), TypedValue(1, E)
    )
    assert abs(ci.value - 1210.0) < 0.01

    cmp = COMPARE_VALUES.execute(TypedValue(200, E), TypedValue(100, E))
    assert cmp.value["a_gt_b"] is True

    print("Finance tests PASSED")


if __name__ == "__main__":
    test_finance_operators()
