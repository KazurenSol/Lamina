"""
Finance equivalence rules for CAS.
Equivalent financial expressions must normalize to same canonical signature.
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_finance_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {"name": "simple_interest_formula",
     "lhs": "P * (1 + r * t)", "rhs": "P + COMPUTE_INTEREST(P, r, t)"},
    {"name": "compound_interest_formula",
     "lhs": "P * (1 + r)^t",   "rhs": "COMPUTE_COMPOUND_INTEREST(P, r, t, 1)"},
    {"name": "balance_after_transactions",
     "lhs": "DEPOSIT + WITHDRAW chain", "rhs": "net UPDATE_BALANCE",
     "condition": "same net amount"},
]
