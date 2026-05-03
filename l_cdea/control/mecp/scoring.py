from __future__ import annotations

from typing import Dict, List

from l_cdea.core.types.base import SemanticType
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from l_cdea.normalization.canonicalizer.signature import CanonicalSignature
from l_cdea.normalization.canonicalizer import CanonicalizationResult
from .exceptions import CostModelError

GainMap = Dict[CanonicalSignature, float]

# Specificity of each output type as a proxy for information value.
# More specific (grounded) types produce higher gain. ABSTRACTION is least informative.
_TYPE_CERTAINTY: Dict[SemanticType, float] = {
    SemanticType.ENTITY:      1.0,
    SemanticType.EVENT:       0.9,
    SemanticType.STATE:       0.8,
    SemanticType.PROCESS:     0.7,
    SemanticType.RELATION:    0.6,
    SemanticType.CONSTRAINT:  0.5,
    SemanticType.ABSTRACTION: 0.2,
}


def compute_gain_map(canonical: CanonicalizationResult) -> GainMap:
    """
    Estimate information gain for each equivalence class.
    Uses one representative graph per class — structurally equivalent graphs yield equal gain.
    No probabilistic model access — structural properties only.
    """
    gain_map: GainMap = {}
    for sig, graphs in canonical.equivalence_map.items():
        if not graphs:
            raise CostModelError(f"Empty equivalence class for signature {sig}")
        representative = graphs[0]
        try:
            gain_map[sig] = _graph_gain(representative)
        except Exception as e:
            raise CostModelError(f"Gain computation failed: {e}") from e
    return gain_map


def _graph_gain(graph: CDLGraph) -> float:
    """
    InformationGain = resolved_type_certainty + structural_compression + dependency_resolution

    resolved_type_certainty:   specificity of the root node's output type
    structural_compression:    unique operator count / total node count (reuse = efficiency)
    dependency_resolution:     ratio of non-leaf nodes (more resolved deps = more information)
    """
    nodes = graph.nodes
    if not nodes:
        return 0.0

    root = _find_root(nodes)
    certainty = _TYPE_CERTAINTY.get(root.operator.signature.output_type, 0.5)

    unique_ops = len({n.operator.name for n in nodes})
    compression = unique_ops / len(nodes)

    non_leaf_ratio = sum(1 for n in nodes if n.inputs) / len(nodes)

    return certainty + compression + non_leaf_ratio


def _find_root(nodes: List[CDLNode]) -> CDLNode:
    """Root = the node not consumed as input by any other node in the graph."""
    consumed: set[int] = set()
    for n in nodes:
        for inp in n.inputs:
            consumed.add(id(inp))
    roots = [n for n in nodes if id(n) not in consumed]
    # In a well-formed DAG there is exactly one root; take the last by operator name for determinism
    return max(roots, key=lambda n: n.operator.name)
