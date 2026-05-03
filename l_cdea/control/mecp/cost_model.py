from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from l_cdea.normalization.canonicalizer.signature import CanonicalSignature
from l_cdea.normalization.canonicalizer import CanonicalizationResult
from .exceptions import CostModelError

# CostMap keys are CanonicalSignatures — all structurally equivalent graphs share a cost.
CostMap = Dict[CanonicalSignature, float]


@dataclass(frozen=True)
class MECPConfig:
    """
    System-level configuration for the MECP cost model.
    All weights are deterministic constants — no runtime randomness allowed.
    """
    alpha: float = 1.0   # structural depth weight
    beta: float = 0.5    # operator complexity weight (input arity)
    gamma: float = 0.3   # branching factor weight
    delta: float = 0.2   # type conversion cost weight (reserved for future use)
    threshold: float = 0.5  # minimum priority to enter execution subset


def compute_cost_map(canonical: CanonicalizationResult, config: MECPConfig) -> CostMap:
    """
    Assign a cost value to each equivalence class.
    Uses one representative graph per class — all members are structurally identical.
    """
    cost_map: CostMap = {}
    for sig, graphs in canonical.equivalence_map.items():
        if not graphs:
            raise CostModelError(f"Empty equivalence class for signature {sig}")
        representative = graphs[0]
        try:
            cost_map[sig] = _graph_cost(representative, config)
        except Exception as e:
            raise CostModelError(f"Cost computation failed: {e}") from e
    return cost_map


def _graph_cost(graph: CDLGraph, config: MECPConfig) -> float:
    """
    Cost(graph) = α*depth + β*operator_complexity + γ*branching_factor + δ*type_conversion_cost
    All terms are structural — no runtime value access.
    """
    nodes = graph.nodes
    if not nodes:
        return 0.0

    depth = _max_depth(nodes)
    non_leaf = [n for n in nodes if n.inputs]

    op_complexity = (
        sum(len(n.operator.signature.input_types) for n in non_leaf) / len(non_leaf)
        if non_leaf else 0.0
    )
    branching = (
        sum(len(n.inputs) for n in non_leaf) / len(non_leaf)
        if non_leaf else 0.0
    )
    type_cost = 0.0  # δ reserved: will reflect inter-type coercion cost in future

    return (
        config.alpha * depth
        + config.beta * op_complexity
        + config.gamma * branching
        + config.delta * type_cost
    )


def _max_depth(nodes: List[CDLNode]) -> int:
    """Max distance from any leaf to the deepest root — structural depth of the DAG."""
    cache: Dict[int, int] = {}

    def depth(node: CDLNode) -> int:
        if id(node) in cache:
            return cache[id(node)]
        result = 0 if not node.inputs else 1 + max(depth(inp) for inp in node.inputs)
        cache[id(node)] = result
        return result

    return max(depth(n) for n in nodes)
