from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)


def _legal(name, inputs, output, fn):
    return CDLOperator(name=f"legal.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


APPLY_RULE = _legal("APPLY_RULE", (C, EV), S,
    lambda rule, case: TypedValue({"rule": rule.value, "case": case.value, "applied": True}, S))

CHECK_CONDITION = _legal("CHECK_CONDITION", (C, E), C,
    lambda condition, context: TypedValue(f"check({condition.value} in {context.value})", C))

EVALUATE_OBLIGATION = _legal("EVALUATE_OBLIGATION", (E, P), S,
    lambda actor, action: TypedValue({"actor": actor.value, "obligation": action.value}, S))

CHECK_PERMISSION = _legal("CHECK_PERMISSION", (E, P), S,
    lambda actor, action: TypedValue({"actor": actor.value, "permitted": action.value, "status": "check_required"}, S))

CHECK_PROHIBITION = _legal("CHECK_PROHIBITION", (E, P), C,
    lambda actor, action: TypedValue({"actor": actor.value, "prohibited": action.value}, C))

DETECT_VIOLATION = _legal("DETECT_VIOLATION", (C, EV), EV,
    lambda rule, case: TypedValue({"violation": True, "rule": rule.value, "case": case.value}, EV))

RESOLVE_CONFLICT = _legal("RESOLVE_CONFLICT", (C, C), P,
    lambda ruleA, ruleB: TypedValue({"conflict_between": [ruleA.value, ruleB.value], "resolution": "pending"}, P))

APPLY_EXCEPTION = _legal("APPLY_EXCEPTION", (C, C), C,
    lambda rule, exception: TypedValue({"base_rule": rule.value, "exception": exception.value}, C))

ESTABLISH_PRECEDENCE = _legal("ESTABLISH_PRECEDENCE", (C, C), C,
    lambda ruleA, ruleB: TypedValue({"higher": ruleA.value, "lower": ruleB.value}, C))

INTERPRET_CLAUSE = _legal("INTERPRET_CLAUSE", (C, E), C,
    lambda clause, context: TypedValue(f"interpret({clause.value} in {context.value})", C))

CLASSIFY_CASE = _legal("CLASSIFY_CASE", (EV,), E,
    lambda case: TypedValue({"case": case.value, "classification": "requires_analysis"}, E))

VALIDATE_COMPLIANCE = _legal("VALIDATE_COMPLIANCE", (EV, E), S,
    lambda case, ruleset: TypedValue({"compliant": "requires_evaluation", "case": case.value, "against": ruleset.value}, S))

ALL_LEGAL_OPERATORS = [
    APPLY_RULE, CHECK_CONDITION, EVALUATE_OBLIGATION, CHECK_PERMISSION, CHECK_PROHIBITION,
    DETECT_VIOLATION, RESOLVE_CONFLICT, APPLY_EXCEPTION, ESTABLISH_PRECEDENCE,
    INTERPRET_CLAUSE, CLASSIFY_CASE, VALIDATE_COMPLIANCE,
]


def register_legal_operators():
    for op in ALL_LEGAL_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
