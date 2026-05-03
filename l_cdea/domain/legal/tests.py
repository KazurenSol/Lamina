def test_legal_operators():
    import l_cdea.domain.legal
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.legal.operators import (
        APPLY_RULE, CHECK_PROHIBITION, DETECT_VIOLATION,
        RESOLVE_CONFLICT, ESTABLISH_PRECEDENCE, VALIDATE_COMPLIANCE,
    )

    assert "legal.APPLY_RULE" in OperatorRegistry.list()
    assert "legal.DETECT_VIOLATION" in OperatorRegistry.list()
    assert "legal.VALIDATE_COMPLIANCE" in OperatorRegistry.list()

    E, P, S, C, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.EVENT)

    rule = TypedValue({"name": "speed_limit", "limit": 65}, C)
    case = TypedValue({"actor": "driver", "speed": 70}, EV)
    result = APPLY_RULE.execute(rule, case)
    assert result.type == S
    assert result.value["applied"] is True

    violation = DETECT_VIOLATION.execute(rule, case)
    assert violation.type == EV
    assert violation.value["violation"] is True

    ruleA = TypedValue({"name": "constitutional_rule", "level": 0}, C)
    ruleB = TypedValue({"name": "local_rule", "level": 4}, C)
    precedence = ESTABLISH_PRECEDENCE.execute(ruleA, ruleB)
    assert precedence.type == C

    print("Legal tests PASSED")


if __name__ == "__main__":
    test_legal_operators()
