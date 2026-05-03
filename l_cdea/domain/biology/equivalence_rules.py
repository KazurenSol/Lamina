"""
Biology equivalence rules for CAS.
Equivalent biological representations must normalize to the same canonical signature.
"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_biology_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)


EQUIVALENCE_RULES = [
    {"name": "central_dogma",
     "lhs": "DNA → RNA → Protein",
     "rhs": "PROTEIN_SYNTHESIS(DNA)"},
    {"name": "photosynthesis_shorthand",
     "lhs": "CONVERT_SUBSTANCE(light+CO2+water, glucose+oxygen)",
     "rhs": "PHOTOSYNTHESIS(inputs)"},
    {"name": "respiration_shorthand",
     "lhs": "CONVERT_SUBSTANCE(glucose+oxygen, ATP+CO2+water)",
     "rhs": "CELL_RESPIRATION(inputs)"},
    {"name": "equivalent_energy_yield",
     "lhs": "multi-step metabolic pathway",
     "rhs": "CELL_RESPIRATION",
     "condition": "same net ATP output"},
]
