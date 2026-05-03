from __future__ import annotations

from dataclasses import dataclass
from typing import List

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from .signature import CanonicalSignature, compute_signature, _canonical_topo_order
from .exceptions import NormalizationError


@dataclass
class NormalizedCDLGraph:
    """
    A CDLGraph in canonical structural form.
    The source graph is never mutated — this is a read-only structural view.
    canonical_node_order is the insertion-order-independent traversal sequence.
    redundant_nodes are pass-through nodes identified for downstream MECP awareness.
    """
    source: CDLGraph
    canonical_node_order: List[CDLNode]
    signature: CanonicalSignature
    redundant_nodes: List[CDLNode]


def normalize(graph: CDLGraph) -> NormalizedCDLGraph:
    """
    Produce a canonical structural view of a CDLGraph.
    - Applies deterministic topological ordering (commutative argument reordering implied)
    - Identifies structurally redundant (pass-through) nodes
    - Does NOT mutate the source graph
    - Does NOT execute any nodes
    """
    if not graph.nodes:
        raise NormalizationError("Cannot normalize an empty CDLGraph")

    try:
        canonical_order = _canonical_topo_order(graph.nodes)
    except Exception as e:
        raise NormalizationError(f"Canonical ordering failed: {e}") from e

    redundant = _find_redundant_nodes(canonical_order)
    sig = compute_signature(graph)

    return NormalizedCDLGraph(
        source=graph,
        canonical_node_order=canonical_order,
        signature=sig,
        redundant_nodes=redundant,
    )


def _find_redundant_nodes(nodes: List[CDLNode]) -> List[CDLNode]:
    """
    A node is structurally redundant (pass-through) if:
    - it has exactly one input
    - its output type equals its single input's output type
    These are candidates for flattening but are never removed here — only flagged.
    """
    redundant = []
    for node in nodes:
        if len(node.inputs) == 1:
            child_out = node.inputs[0].operator.signature.output_type
            node_out = node.operator.signature.output_type
            if child_out == node_out:
                redundant.append(node)
    return redundant
