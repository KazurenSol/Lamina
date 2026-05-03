"""Geographic equivalence: CAPITAL_OF(X) = GEO_LOOKUP(X, capital_mapping)"""
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.normalization.canonicalizer.signature import compute_signature


def are_geo_equivalent(g1: CDLGraph, g2: CDLGraph) -> bool:
    return compute_signature(g1) == compute_signature(g2)
