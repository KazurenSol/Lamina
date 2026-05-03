"""
Math equivalence rules for CAS.
Equivalent expressions must normalize to the same canonical signature.
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_math_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {"name": "commutativity_add",  "lhs": "a + b",       "rhs": "b + a"},
    {"name": "commutativity_mul",  "lhs": "a * b",       "rhs": "b * a"},
    {"name": "associativity_add",  "lhs": "(a+b)+c",     "rhs": "a+(b+c)"},
    {"name": "distributive",       "lhs": "2*(a+b)",     "rhs": "2a + 2b"},
    {"name": "perfect_square",     "lhs": "x^2+2x+1",   "rhs": "(x+1)^2"},
    {"name": "div_as_inv_mul",     "lhs": "a/b",         "rhs": "a*b^-1"},
    {"name": "factor_difference",  "lhs": "a^2 - b^2",  "rhs": "(a+b)*(a-b)"},
]
