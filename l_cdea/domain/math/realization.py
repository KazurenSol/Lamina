"""
Math realization engine — the entry point for all symbolic math transformations.

Public API:
  realize_simplify(text: str) → MathTrace
  realize_expand(text: str)   → MathTrace
  parse_expr(text: str)       → Expr
  to_string(expr: Expr)       → str

MathTrace carries full observability: input, parsed AST repr, rules fired, output.

Design rules (from spec):
  - No external CAS (no sympy)
  - No randomness
  - No floating-point drift
  - All transformations exact and deterministic
  - Output is canonical
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from l_cdea.domain.math.ast import Expr, Const, Var, Add, Mul, Pow
from l_cdea.domain.math.normalizer import normalize
from l_cdea.domain.math.rules import simplify_to_fixpoint, expand_to_fixpoint


# ── Trace ─────────────────────────────────────────────────────────────────────

@dataclass
class MathTrace:
    """Observability record for a single math realization pass."""
    input_expression: str
    parsed_ast: str = ""                         # repr(ast) before any transforms
    applied_rules_sequence: List[str] = field(default_factory=list)
    final_ast: str = ""
    output_expression: str = ""
    error: Optional[str] = None


# ── Tokenizer ─────────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?"       # numbers (int or float)
    r"|[a-zA-Z]\w*"        # identifiers / variables
    r"|[+\-\*/\^()]"       # operators and parens
)


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text)


# ── Parser (recursive descent) ────────────────────────────────────────────────

class _Parser:
    """
    Grammar (highest precedence first):
      atom   ::= number | var | '(' expr ')'
      power  ::= atom ('^' power)?         [right-associative]
      unary  ::= '-' unary | power
      term   ::= unary ('*' unary)*
      expr   ::= term (('+' | '-') term)*
    """

    def __init__(self, tokens: List[str]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Optional[str]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self, expected: Optional[str] = None) -> str:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if expected is not None and tok != expected:
            raise ValueError(f"Expected '{expected}', got '{tok}'")
        self._pos += 1
        return tok

    def parse(self) -> Expr:
        result = self._expr()
        if self._pos < len(self._tokens):
            raise ValueError(
                f"Unexpected token '{self._peek()}' at position {self._pos}"
            )
        return result

    def _expr(self) -> Expr:
        left = self._term()
        while self._peek() in ("+", "-"):
            op = self._consume()
            right = self._term()
            if op == "+":
                left = Add(left, right)
            else:
                # a - b  ≡  a + ((-1) * b)
                left = Add(left, Mul(Const(-1), right))
        return left

    def _term(self) -> Expr:
        left = self._unary()
        while self._peek() == "*":
            self._consume("*")
            right = self._unary()
            left = Mul(left, right)
        return left

    def _unary(self) -> Expr:
        if self._peek() == "-":
            self._consume("-")
            operand = self._unary()
            return Mul(Const(-1), operand)
        return self._power()

    def _power(self) -> Expr:
        base = self._atom()
        if self._peek() == "^":
            self._consume("^")
            exp = self._power()  # right-associative
            return Pow(base, exp)
        return base

    def _atom(self) -> Expr:
        tok = self._peek()
        if tok is None:
            raise ValueError("Expected an expression, got end of input")
        if tok == "(":
            self._consume("(")
            e = self._expr()
            self._consume(")")
            return e
        # Number
        if re.match(r"^\d", tok):
            self._consume()
            return Const(float(tok) if "." in tok else int(tok))
        # Variable / identifier
        if re.match(r"^[a-zA-Z]", tok):
            self._consume()
            return Var(tok)
        raise ValueError(f"Unexpected token: '{tok}'")


def parse_expr(text: str) -> Expr:
    """Parse a math expression string into an AST.  Raises ValueError on syntax errors."""
    tokens = _tokenize(text.strip())
    if not tokens:
        raise ValueError("Empty expression")
    return _Parser(tokens).parse()


# ── Canonical string printer ──────────────────────────────────────────────────

def to_string(expr: Expr) -> str:
    """
    Convert an AST to canonical string form.

    Precedence and parenthesization:
      - Atoms (Const, Var) — no parens
      - Pow — wraps Add/Mul base in parens
      - Mul — wraps Add sub-expressions in parens
      - Add — no parens needed at top level

    Compact notation:
      Mul(Const(n), Var(x)) → "nx"     (e.g. "2x", "3y")
      Mul(Const(-1), x)    → "-x"
    """
    if isinstance(expr, Const):
        v = expr.value
        return str(int(v)) if isinstance(v, float) and v == int(v) else str(v)

    if isinstance(expr, Var):
        return expr.name

    if isinstance(expr, Add):
        left_s = to_string(expr.left)
        right_s = to_string(expr.right)
        # Render "a + -b" more naturally as "a - b"
        if right_s.startswith("-"):
            return f"{left_s} - {right_s[1:]}"
        return f"{left_s} + {right_s}"

    if isinstance(expr, Mul):
        # Compact: -1 * x → "-x"
        if isinstance(expr.left, Const) and expr.left.value == -1:
            inner = to_string(expr.right)
            return f"-{inner}" if not inner.startswith("(") else f"-{inner}"

        # Compact: Const(n) * Var(x) → "nx"
        if isinstance(expr.left, Const) and isinstance(expr.right, Var):
            return f"{to_string(expr.left)}{expr.right.name}"

        left_s = _mul_operand(expr.left)
        right_s = _mul_operand(expr.right)
        return f"{left_s} * {right_s}"

    if isinstance(expr, Pow):
        base_s = _pow_base(expr.base)
        exp_s = _pow_exp(expr.exp)
        return f"{base_s}^{exp_s}"

    raise ValueError(f"Unknown expression type: {type(expr).__name__}")


def _mul_operand(e: Expr) -> str:
    """Parenthesize Add when it appears as a Mul operand."""
    s = to_string(e)
    if isinstance(e, Add):
        return f"({s})"
    return s


def _pow_base(e: Expr) -> str:
    """Parenthesize Add/Mul when they appear as a Pow base."""
    s = to_string(e)
    if isinstance(e, (Add, Mul)):
        return f"({s})"
    return s


def _pow_exp(e: Expr) -> str:
    """Parenthesize compound expressions in exponent position."""
    s = to_string(e)
    if isinstance(e, (Add, Mul, Pow)):
        return f"({s})"
    return s


# ── Main API ──────────────────────────────────────────────────────────────────

def realize_simplify(text: str) -> MathTrace:
    """
    Full simplification pipeline:
      parse → normalize → simplify-to-fixpoint → to_string

    Returns MathTrace with observability data.
    """
    trace = MathTrace(input_expression=text)
    try:
        ast = parse_expr(text)
        trace.parsed_ast = repr(ast)

        ast = normalize(ast)
        ast, rules = simplify_to_fixpoint(ast)
        ast = normalize(ast)   # re-normalize: simplification may create new Consts

        trace.applied_rules_sequence = rules
        trace.final_ast = repr(ast)
        trace.output_expression = to_string(ast)
    except Exception as exc:
        trace.error = str(exc)
        trace.output_expression = text  # pass-through on failure
    return trace


def realize_expand(text: str) -> MathTrace:
    """
    Full expansion pipeline:
      parse → normalize → expand-to-fixpoint (includes simplification) → normalize → to_string
    """
    trace = MathTrace(input_expression=text)
    try:
        ast = parse_expr(text)
        trace.parsed_ast = repr(ast)

        ast = normalize(ast)
        ast, rules = expand_to_fixpoint(ast)
        ast = normalize(ast)   # re-normalize after expansion

        trace.applied_rules_sequence = rules
        trace.final_ast = repr(ast)
        trace.output_expression = to_string(ast)
    except Exception as exc:
        trace.error = str(exc)
        trace.output_expression = text
    return trace
