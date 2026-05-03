"""
Algebraic transformation helpers for the math domain.
All functions are deterministic and pure.
"""
from l_cdea.core.types.base import SemanticType, TypedValue

E = SemanticType.ENTITY
P = SemanticType.PROCESS
C = SemanticType.CONSTRAINT


def expand_binomial(a, b, n=2):
    """Expand (a + b)^n for small integer n."""
    if n == 2:
        return f"({a})^2 + 2*({a})*({b}) + ({b})^2"
    return f"expand(({a}+{b})^{n})"


def factor_quadratic(a, b, c):
    """Attempt to factor ax^2 + bx + c."""
    if a == 1:
        discriminant = b * b - 4 * c
        if discriminant >= 0:
            import math
            sqrt_d = math.isqrt(discriminant)
            if sqrt_d * sqrt_d == discriminant:
                r1 = (-b + sqrt_d) // 2
                r2 = (-b - sqrt_d) // 2
                return f"(x - {r1})(x - {r2})"
    return f"factor({a}x^2 + {b}x + {c})"


ALGEBRAIC_IDENTITIES = [
    {"name": "commutativity_add",  "lhs": "a + b",  "rhs": "b + a"},
    {"name": "commutativity_mul",  "lhs": "a * b",  "rhs": "b * a"},
    {"name": "associativity_add",  "lhs": "(a + b) + c", "rhs": "a + (b + c)"},
    {"name": "distributive",       "lhs": "a * (b + c)", "rhs": "a*b + a*c"},
    {"name": "difference_squares", "lhs": "a^2 - b^2", "rhs": "(a+b)(a-b)"},
    {"name": "perfect_square",     "lhs": "(a+b)^2", "rhs": "a^2 + 2ab + b^2"},
]
