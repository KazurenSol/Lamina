"""
Basic symbolic calculus helpers for the math domain (V1).
Deterministic, no numerical approximation without explicit flag.
"""

DERIVATIVE_RULES = [
    {"name": "power_rule",    "pattern": "x^n",      "result": "n*x^(n-1)"},
    {"name": "constant_rule", "pattern": "c",         "result": "0"},
    {"name": "sum_rule",      "pattern": "f + g",     "result": "f' + g'"},
    {"name": "product_rule",  "pattern": "f * g",     "result": "f'*g + f*g'"},
    {"name": "chain_rule",    "pattern": "f(g(x))",   "result": "f'(g(x)) * g'(x)"},
]

INTEGRAL_RULES = [
    {"name": "power_rule",    "pattern": "x^n",      "result": "x^(n+1)/(n+1) + C"},
    {"name": "constant_rule", "pattern": "c",         "result": "c*x + C"},
    {"name": "sum_rule",      "pattern": "f + g",     "result": "∫f + ∫g"},
]


def symbolic_derivative(expr: str, var: str) -> str:
    """Return symbolic derivative notation; actual symbolic computation deferred to CAS."""
    return f"d/d{var}({expr})"


def symbolic_integral(expr: str, var: str) -> str:
    """Return symbolic integral notation."""
    return f"∫({expr})d{var}"
