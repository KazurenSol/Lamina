"""
Physics equivalence rules for CAS.
Physical identities that yield the same canonical signature.
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_physics_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {"name": "newton_rearrangement", "lhs": "F = m*a",              "rhs": "a = F/m"},
    {"name": "ke_variable_rename",   "lhs": "0.5*m*v^2",            "rhs": "0.5*mass*velocity^2"},
    {"name": "position_integrate",   "lhs": "x + v*t",              "rhs": "INTEGRATE(x, v, t)"},
    {"name": "multi_step_collapse",  "lhs": "chain of intermediate states", "rhs": "final state",
     "condition": "intermediate states not observed"},
]
