"""
Legal equivalence rules for CAS.
Logically equivalent clauses and reordered conditions must normalize to the same signature.
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_legal_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {"name": "and_commutativity",     "lhs": "IF A AND B THEN X",      "rhs": "IF B AND A THEN X"},
    {"name": "double_negation",       "lhs": "NOT (NOT A)",            "rhs": "A"},
    {"name": "conditional_flatten",   "lhs": "IF A THEN (IF B THEN X)", "rhs": "IF A AND B THEN X"},
    {"name": "demorgan_and",          "lhs": "NOT (A AND B)",          "rhs": "NOT A OR NOT B"},
    {"name": "demorgan_or",           "lhs": "NOT (A OR B)",           "rhs": "NOT A AND NOT B"},
]
