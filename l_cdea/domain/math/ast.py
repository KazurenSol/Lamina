"""
Symbolic expression AST for the math realization engine.

Node types:
  Const(value)         — numeric constant
  Var(name)            — symbolic variable
  Add(left, right)     — addition
  Mul(left, right)     — multiplication
  Pow(base, exp)       — exponentiation

All nodes are frozen dataclasses (hashable, immutable, value-equal).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


class Expr:
    """Abstract base for all expression nodes."""
    __slots__ = ()


@dataclass(frozen=True)
class Const(Expr):
    """Numeric constant.  value must be int or float."""
    value: Union[int, float]

    def __post_init__(self):
        # Coerce whole-number floats to int so Const(2.0) == Const(2)
        if isinstance(self.value, float) and self.value == int(self.value):
            object.__setattr__(self, "value", int(self.value))


@dataclass(frozen=True)
class Var(Expr):
    """Symbolic variable — a named unknown."""
    name: str


@dataclass(frozen=True)
class Add(Expr):
    """Binary addition: left + right."""
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Mul(Expr):
    """Binary multiplication: left * right."""
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Pow(Expr):
    """Exponentiation: base ^ exp."""
    base: Expr
    exp: Expr
