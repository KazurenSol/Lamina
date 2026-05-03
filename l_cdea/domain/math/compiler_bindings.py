from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                  SemanticType.CONSTRAINT, SemanticType.ABSTRACTION)

MATH_FRAME_MAPPINGS = {
    "ADD_QUERY":               [((E, E), E)],
    "SUBTRACT_QUERY":          [((E, E), E)],
    "MULTIPLY_QUERY":          [((E, E), E)],
    "DIVIDE_QUERY":            [((E, E), E)],
    "POWER_QUERY":             [((E, E), E)],
    "SIMPLIFY_QUERY":          [((P,), P)],
    "EXPAND_QUERY":            [((P,), P)],
    "FACTOR_QUERY":            [((P,), P)],
    "SOLVE_QUERY":             [((C, E), E)],
    "DERIVE_QUERY":            [((P, E), P)],
    "INTEGRATE_QUERY":         [((P, E), P)],
    "DEFINE_FUNCTION_QUERY":   [((A, E, P), P)],
    "EVALUATE_FUNCTION_QUERY": [((P, E), E)],
    "IS_EQUAL_QUERY":          [((E, E), C)],
    "COMPARE_QUERY":           [((E, E), C)],
    "UNION_QUERY":             [((E, E), E)],
    "INTERSECTION_QUERY":      [((E, E), E)],
    "CONTAINS_QUERY":          [((E, E), C)],
}


def register_math_bindings():
    _FRAME_TYPE_MAP.update(MATH_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="math.simplify", domain="math", operator_name="SIMPLIFY",
                    keywords=("simplify",), required_slots=("expression",), optional_slots=(), priority=100),
        PatternRule(id="math.expand", domain="math", operator_name="EXPAND",
                    keywords=("expand",), required_slots=("expression",), optional_slots=(), priority=100),
        PatternRule(id="math.factor", domain="math", operator_name="FACTOR",
                    keywords=("factor",), required_slots=("expression",), optional_slots=(), priority=100),
        PatternRule(id="math.solve", domain="math", operator_name="SOLVE",
                    keywords=("solve",), required_slots=("expression",), optional_slots=("variable",), priority=95),
        PatternRule(id="math.derive", domain="math", operator_name="DERIVE",
                    keywords=("differentiate",), required_slots=("expression",), optional_slots=("variable",), priority=95),
        PatternRule(id="math.integrate", domain="math", operator_name="INTEGRATE",
                    keywords=("integrate",), required_slots=("expression",), optional_slots=("variable",), priority=95),
        PatternRule(id="math.add", domain="math", operator_name="ADD",
                    keywords=("add",), required_slots=(), optional_slots=(), priority=80),
        PatternRule(id="math.evaluate_fn", domain="math", operator_name="EVALUATE_FUNCTION",
                    keywords=("evaluate",), required_slots=("expression",), optional_slots=(), priority=85),
    ]
    for rule in rules:
        registry.register(rule)
