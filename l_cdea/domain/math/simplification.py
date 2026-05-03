"""
Math simplification rules applied by the SIMPLIFY operator.
Rules are deterministic and order-independent in their application.
"""

SIMPLIFICATION_RULES = [
    {"pattern": "x + 0",  "result": "x",  "name": "additive_identity"},
    {"pattern": "x * 1",  "result": "x",  "name": "multiplicative_identity"},
    {"pattern": "x * 0",  "result": "0",  "name": "zero_product"},
    {"pattern": "x - x",  "result": "0",  "name": "self_subtraction"},
    {"pattern": "x / x",  "result": "1",  "name": "self_division"},
    {"pattern": "x^1",    "result": "x",  "name": "power_one"},
    {"pattern": "x^0",    "result": "1",  "name": "power_zero"},
    {"pattern": "0 + x",  "result": "x",  "name": "zero_addend"},
    {"pattern": "1 * x",  "result": "x",  "name": "unit_factor"},
]


def apply_simplifications(expr: str) -> str:
    """Apply string-level simplification rules to a symbolic expression."""
    for rule in SIMPLIFICATION_RULES:
        pattern = rule["pattern"].replace("x", "(.+?)")
        expr = expr.replace(rule["pattern"], rule["result"])
    return expr
