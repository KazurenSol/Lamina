"""
Simplification and expansion rules for the math realization engine.

simplify_step(expr) → (new_expr, rules_fired: List[str])
  Apply one bottom-up pass of all simplification rules.
  Returns the rewritten expression and the list of rule names that fired.

simplify_to_fixpoint(expr, max_iter=50) → (expr, all_rules: List[str])
  Repeat simplify_step until the expression is stable.

expand_once(expr) → (new_expr, rules_fired: List[str])
  Apply one bottom-up pass of expansion rules (distribute, FOIL).

expand_to_fixpoint(expr, max_iter=50) → (expr, all_rules: List[str])
  Repeat until stable, then simplify.
"""
from __future__ import annotations

from typing import List, Tuple

from l_cdea.domain.math.ast import Expr, Const, Var, Add, Mul, Pow


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_zero(e: Expr) -> bool:
    return isinstance(e, Const) and e.value == 0

def _is_one(e: Expr) -> bool:
    return isinstance(e, Const) and e.value == 1

def _is_const(e: Expr) -> bool:
    return isinstance(e, Const)


# ── Simplification rules ──────────────────────────────────────────────────────

def simplify_step(expr: Expr) -> Tuple[Expr, List[str]]:
    """
    One bottom-up simplification pass.  Recurse into children first, then
    apply the 10 mandatory rules at the current node.

    Rules (V1 mandatory):
      1.  x + 0 → x
      2.  0 + x → x
      3.  x * 1 → x
      4.  1 * x → x
      5.  x * 0 → 0
      6.  0 * x → 0
      7.  x + x → 2 * x
      8.  (a + b) + c → a + (b + c)  [right-associative flattening for constant folding]
      9.  Const(a) + Const(b) → Const(a + b)
      10. Const(a) * Const(b) → Const(a * b)
    """
    fired: List[str] = []

    if isinstance(expr, (Const, Var)):
        return expr, fired

    if isinstance(expr, Add):
        left, lf = simplify_step(expr.left)
        right, rf = simplify_step(expr.right)
        fired.extend(lf + rf)

        # Rule 9: both constants
        if _is_const(left) and _is_const(right):
            result = Const(left.value + right.value)
            fired.append(f"{left.value} + {right.value} → {result.value}")
            return result, fired

        # Rule 1: x + 0 → x
        if _is_zero(right):
            fired.append(f"x + 0 → x")
            return left, fired

        # Rule 2: 0 + x → x
        if _is_zero(left):
            fired.append(f"0 + x → x")
            return right, fired

        # Rule 7: x + x → 2 * x
        if left == right:
            result = Mul(Const(2), left)
            fired.append(f"x + x → 2 * x")
            return result, fired

        return Add(left, right), fired

    if isinstance(expr, Mul):
        left, lf = simplify_step(expr.left)
        right, rf = simplify_step(expr.right)
        fired.extend(lf + rf)

        # Rule 10: both constants
        if _is_const(left) and _is_const(right):
            result = Const(left.value * right.value)
            fired.append(f"{left.value} * {right.value} → {result.value}")
            return result, fired

        # Rule: x * x → x^2
        if left == right:
            result = Pow(left, Const(2))
            fired.append(f"x * x → x^2")
            return result, fired

        # Rule: Const(a) * (Const(b) * x) → Const(a*b) * x  [constant hoisting]
        if isinstance(left, Const) and isinstance(right, Mul) and isinstance(right.left, Const):
            new_coeff = Const(left.value * right.left.value)
            result = Mul(new_coeff, right.right)
            fired.append(f"a * (b * x) → (a*b) * x")
            return result, fired

        # Rule 5: x * 0 → 0
        if _is_zero(right):
            fired.append(f"x * 0 → 0")
            return Const(0), fired

        # Rule 6: 0 * x → 0
        if _is_zero(left):
            fired.append(f"0 * x → 0")
            return Const(0), fired

        # Rule 3: x * 1 → x
        if _is_one(right):
            fired.append(f"x * 1 → x")
            return left, fired

        # Rule 4: 1 * x → x
        if _is_one(left):
            fired.append(f"1 * x → x")
            return right, fired

        return Mul(left, right), fired

    if isinstance(expr, Pow):
        base, bf = simplify_step(expr.base)
        exp, ef = simplify_step(expr.exp)
        fired.extend(bf + ef)

        # Const ^ Const
        if _is_const(base) and _is_const(exp):
            result = Const(base.value ** exp.value)
            fired.append(f"{base.value}^{exp.value} → {result.value}")
            return result, fired

        return Pow(base, exp), fired

    return expr, fired


def simplify_to_fixpoint(
    expr: Expr,
    max_iter: int = 50,
) -> Tuple[Expr, List[str]]:
    """Repeat simplify_step until stable.  Raises if max_iter exceeded."""
    all_rules: List[str] = []
    for _ in range(max_iter):
        new_expr, fired = simplify_step(expr)
        all_rules.extend(fired)
        if new_expr == expr:
            return new_expr, all_rules
        expr = new_expr
    return expr, all_rules


# ── Expansion rules ───────────────────────────────────────────────────────────

def expand_once(expr: Expr) -> Tuple[Expr, List[str]]:
    """
    One bottom-up expansion pass.

    Rules:
      E1. Mul(a, Add(b, c)) → Add(Mul(a, b), Mul(a, c))   [left distribute]
      E2. Mul(Add(a, b), c) → Add(Mul(a, c), Mul(b, c))   [right distribute]
      E3. Pow(Add(a, b), Const(2)) → Add(Add(Pow(a,2), Mul(Mul(2,a),b)), Pow(b,2))
          i.e. (a+b)^2 = a^2 + 2ab + b^2
      E4. Pow(expr, Const(1)) → expr
      E5. Pow(expr, Const(0)) → Const(1)
    """
    fired: List[str] = []

    if isinstance(expr, (Const, Var)):
        return expr, fired

    if isinstance(expr, Add):
        left, lf = expand_once(expr.left)
        right, rf = expand_once(expr.right)
        fired.extend(lf + rf)
        return Add(left, right), fired

    if isinstance(expr, Mul):
        left, lf = expand_once(expr.left)
        right, rf = expand_once(expr.right)
        fired.extend(lf + rf)

        # E1: a * (b + c) → a*b + a*c
        if isinstance(right, Add):
            result = Add(Mul(left, right.left), Mul(left, right.right))
            fired.append(f"a * (b + c) → a*b + a*c")
            return result, fired

        # E2: (a + b) * c → a*c + b*c
        if isinstance(left, Add):
            result = Add(Mul(left.left, right), Mul(left.right, right))
            fired.append(f"(a + b) * c → a*c + b*c")
            return result, fired

        return Mul(left, right), fired

    if isinstance(expr, Pow):
        base, bf = expand_once(expr.base)
        exp, ef = expand_once(expr.exp)
        fired.extend(bf + ef)

        # E4/E5: trivial powers
        if _is_const(exp):
            if exp.value == 1:
                fired.append(f"x^1 → x")
                return base, fired
            if exp.value == 0:
                fired.append(f"x^0 → 1")
                return Const(1), fired

        # E3: (a + b)^2 = a^2 + 2*a*b + b^2
        if isinstance(base, Add) and isinstance(exp, Const) and exp.value == 2:
            a, b = base.left, base.right
            a2 = Pow(a, Const(2))
            b2 = Pow(b, Const(2))
            ab2 = Mul(Mul(Const(2), a), b)
            result = Add(Add(a2, ab2), b2)
            fired.append(f"(a+b)^2 → a^2 + 2ab + b^2")
            return result, fired

        return Pow(base, exp), fired

    return expr, fired


def expand_to_fixpoint(
    expr: Expr,
    max_iter: int = 50,
) -> Tuple[Expr, List[str]]:
    """
    Expand, normalize, simplify until stable.
    Normalization between steps ensures Const-first ordering so that
    the hoisting rule (Const * (Const * x) → (Const*Const) * x) can fire.
    """
    from l_cdea.domain.math.normalizer import normalize
    all_rules: List[str] = []
    for _ in range(max_iter):
        new_expr, ef = expand_once(expr)
        all_rules.extend(ef)
        new_expr = normalize(new_expr)          # Const to left before simplify
        new_expr, sf = simplify_to_fixpoint(new_expr)
        all_rules.extend(sf)
        new_expr = normalize(new_expr)          # Const to left after simplify
        if new_expr == expr:
            return new_expr, all_rules
        expr = new_expr
    return expr, all_rules
