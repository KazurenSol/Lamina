"""
Expression normalizer — produces a canonical tree form before simplification.

Rules applied bottom-up:
  1. In Mul, put Const on the left  (2 * x, not x * 2)
  2. In Add/Mul, sort commutative operands by canonical_key()
     so that a + b == b + a in canonical form.
  3. Flatten nested Add chains: (a + (b + c)) → ((a + b) + c)
     (left-associative canonical form, so to_string reads left-to-right)

Sorting key priority (low → high, i.e. sorted first):
  Const < Var < compound expressions (Mul, Pow, Add)
  Within each class: sort by string representation.
"""
from __future__ import annotations

from l_cdea.domain.math.ast import Expr, Const, Var, Add, Mul, Pow


def canonical_key(expr: Expr) -> tuple:
    """
    Return a tuple key for deterministic ordering of expressions.
    Consts sort before Vars, which sort before compounds.
    """
    if isinstance(expr, Const):
        return (0, expr.value, "")
    if isinstance(expr, Var):
        return (1, 0, expr.name)
    if isinstance(expr, Mul):
        return (2, 0, f"mul:{canonical_key(expr.left)}:{canonical_key(expr.right)}")
    if isinstance(expr, Pow):
        return (3, 0, f"pow:{canonical_key(expr.base)}:{canonical_key(expr.exp)}")
    if isinstance(expr, Add):
        return (4, 0, f"add:{canonical_key(expr.left)}:{canonical_key(expr.right)}")
    return (9, 0, str(expr))


def normalize(expr: Expr) -> Expr:
    """
    Normalize expr bottom-up.  Returns a structurally equivalent expression
    in canonical form.  Idempotent.

    Policy:
    - Add: do NOT sort children — preserves polynomial order (x^2 + 2x + 1)
           and avoids scrambling expansion output.  The simplification rules
           handle both operand orderings explicitly (rules 1+2, 5+6, etc.).
    - Mul: put Const on the left for compact notation (2x, not x2).
    """
    if isinstance(expr, (Const, Var)):
        return expr

    if isinstance(expr, Add):
        return Add(normalize(expr.left), normalize(expr.right))

    if isinstance(expr, Mul):
        left = normalize(expr.left)
        right = normalize(expr.right)
        # Move Const to the left: Const * x (not x * Const)
        if isinstance(right, Const) and not isinstance(left, Const):
            left, right = right, left
        return Mul(left, right)

    if isinstance(expr, Pow):
        return Pow(normalize(expr.base), normalize(expr.exp))

    return expr
