from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)

LEGAL_FRAME_MAPPINGS = {
    "APPLY_RULE_QUERY":          [((C, EV), S)],
    "CHECK_CONDITION_QUERY":     [((C, E), C)],
    "EVALUATE_OBLIGATION_QUERY": [((E, P), S)],
    "CHECK_PERMISSION_QUERY":    [((E, P), S)],
    "CHECK_PROHIBITION_QUERY":   [((E, P), C)],
    "DETECT_VIOLATION_QUERY":    [((C, EV), EV)],
    "RESOLVE_CONFLICT_QUERY":    [((C, C), P)],
    "APPLY_EXCEPTION_QUERY":     [((C, C), C)],
    "ESTABLISH_PRECEDENCE_QUERY":[((C, C), C)],
    "INTERPRET_CLAUSE_QUERY":    [((C, E), C)],
    "CLASSIFY_CASE_QUERY":       [((EV,), E)],
    "VALIDATE_COMPLIANCE_QUERY": [((EV, E), S)],
}


def register_legal_bindings():
    _FRAME_TYPE_MAP.update(LEGAL_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="legal.check_prohibition.illegal", domain="legal", operator_name="CHECK_PROHIBITION",
                    keywords=("illegal",), required_slots=(), optional_slots=("action",), priority=105),
        PatternRule(id="legal.check_prohibition.prohibited", domain="legal", operator_name="CHECK_PROHIBITION",
                    keywords=("prohibited",), required_slots=(), optional_slots=("action",), priority=105),
        PatternRule(id="legal.check_permission.legal", domain="legal", operator_name="CHECK_PERMISSION",
                    keywords=("legal",), required_slots=(), optional_slots=("actor", "action"), priority=100),
        PatternRule(id="legal.check_permission.allowed", domain="legal", operator_name="CHECK_PERMISSION",
                    keywords=("allowed",), required_slots=(), optional_slots=("actor", "action"), priority=100),
        PatternRule(id="legal.check_permission.permitted", domain="legal", operator_name="CHECK_PERMISSION",
                    keywords=("permitted",), required_slots=(), optional_slots=("actor", "action"), priority=100),
        PatternRule(id="legal.detect_violation", domain="legal", operator_name="DETECT_VIOLATION",
                    keywords=("violation", "violated"), required_slots=(), optional_slots=("rule", "case"), priority=105),
        PatternRule(id="legal.resolve_conflict", domain="legal", operator_name="RESOLVE_CONFLICT",
                    keywords=("conflict", "resolve"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="legal.establish_precedence", domain="legal", operator_name="ESTABLISH_PRECEDENCE",
                    keywords=("override", "precedence"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="legal.validate_compliance", domain="legal", operator_name="VALIDATE_COMPLIANCE",
                    keywords=("compliant", "compliance"), required_slots=(), optional_slots=("case", "rule"), priority=100),
        PatternRule(id="legal.apply_rule", domain="legal", operator_name="APPLY_RULE",
                    keywords=("apply", "rule"), required_slots=(), optional_slots=("rule", "case"), priority=90),
        PatternRule(id="legal.classify_case", domain="legal", operator_name="CLASSIFY_CASE",
                    keywords=("classify", "case"), required_slots=(), optional_slots=(), priority=90),
    ]
    for rule in rules:
        registry.register(rule)
