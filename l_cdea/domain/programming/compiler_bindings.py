from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)

PROGRAMMING_FRAME_MAPPINGS = {
    "DEFINE_VARIABLE_QUERY":   [((A, E), E)],
    "ASSIGN_QUERY":            [((E, E), S)],
    "DEFINE_FUNCTION_QUERY":   [((A, E, P), P)],
    "CALL_FUNCTION_QUERY":     [((P, E), E)],
    "RETURN_VALUE_QUERY":      [((E,), S)],
    "EVALUATE_EXPRESSION_QUERY": [((P,), E)],
    "CONDITIONAL_BRANCH_QUERY": [((C, P, P), P)],
    "ITERATE_QUERY":           [((E, P), P)],
    "INDEX_QUERY":             [((E, E), E)],
    "LOOKUP_KEY_QUERY":        [((E, E), E)],
    "COMPARE_VALUES_QUERY":    [((E, E, A), C)],
    "RAISE_ERROR_QUERY":       [((A, E), EV)],
    "HANDLE_ERROR_QUERY":      [((EV, P), S)],
}


def register_programming_bindings():
    _FRAME_TYPE_MAP.update(PROGRAMMING_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="prog.lookup_key", domain="programming", operator_name="LOOKUP_KEY",
                    keywords=("lookup", "dictionary"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="prog.lookup_key.get", domain="programming", operator_name="LOOKUP_KEY",
                    keywords=("get", "from"), required_slots=(), optional_slots=(), priority=85),
        PatternRule(id="prog.iterate", domain="programming", operator_name="ITERATE",
                    keywords=("iterate", "loop"), required_slots=(), optional_slots=("collection",), priority=95),
        PatternRule(id="prog.find_first", domain="programming", operator_name="ITERATE",
                    keywords=("find", "first", "in"), required_slots=("predicate", "collection"), optional_slots=(), priority=105),
        PatternRule(id="prog.filter", domain="programming", operator_name="FILTER",
                    keywords=("filter",), required_slots=(), optional_slots=("collection",), priority=95),
        PatternRule(id="prog.define_function", domain="programming", operator_name="DEFINE_FUNCTION",
                    keywords=("function", "returns"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="prog.conditional", domain="programming", operator_name="CONDITIONAL_BRANCH",
                    keywords=("if",), required_slots=(), optional_slots=(), priority=80),
        PatternRule(id="prog.compare", domain="programming", operator_name="COMPARE_VALUES",
                    keywords=("compare",), required_slots=(), optional_slots=(), priority=80),
    ]
    for rule in rules:
        registry.register(rule)
