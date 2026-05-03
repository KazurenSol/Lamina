from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from .exceptions import EquivalenceDetectionError


@dataclass(frozen=True)
class NodeSignature:
    """Structural fingerprint of one graph node. Value-free — types and shape only."""
    operator_name: str
    input_types: Tuple[str, ...]
    output_type: str
    input_indices: Tuple[int, ...]  # positions in topological order


@dataclass(frozen=True)
class CanonicalSignature:
    """
    Hashable structural fingerprint of an entire CDLGraph.
    Two graphs with identical CanonicalSignature are structurally equivalent.
    Built from topological node order — insertion order independent.
    """
    nodes: Tuple[NodeSignature, ...]


def _node_sort_key(node: CDLNode) -> str:
    """Stable sort key for a node — leaf nodes sort before operator nodes."""
    if node.operator is None:
        return f"\x00leaf:{node.value.type.value if node.value else 'none'}"
    return node.operator.name


def compute_signature(graph: CDLGraph) -> CanonicalSignature:
    """
    Convert a CDLGraph into its canonical structural signature.
    Uses operator names and TypeSignatures only — never runtime values.
    Leaf nodes (operator=None) are represented as "_leaf_<type>".
    """
    try:
        order = _canonical_topo_order(graph.nodes)
    except Exception as e:
        raise EquivalenceDetectionError(f"Signature computation failed: {e}") from e

    index: Dict[int, int] = {id(n): i for i, n in enumerate(order)}
    node_sigs: List[NodeSignature] = []

    for node in order:
        if node.operator is None:
            # Leaf node: structural placeholder using the value's type
            vtype = node.value.type.value if node.value else "unknown"
            node_sigs.append(NodeSignature(
                operator_name=f"_leaf_{vtype}",
                input_types=(),
                output_type=vtype,
                input_indices=(),
            ))
        else:
            node_sigs.append(NodeSignature(
                operator_name=node.operator.name,
                input_types=tuple(t.value for t in node.operator.signature.input_types),
                output_type=node.operator.signature.output_type.value,
                input_indices=tuple(index[id(inp)] for inp in node.inputs),
            ))

    return CanonicalSignature(nodes=tuple(node_sigs))


def _canonical_topo_order(nodes: List[CDLNode]) -> List[CDLNode]:
    """
    Topological sort with deterministic tie-breaking.
    Leaf nodes (operator=None) sort before operator nodes.
    """
    visited: Set[int] = set()
    order: List[CDLNode] = []

    def visit(node: CDLNode):
        if id(node) in visited:
            return
        visited.add(id(node))
        for inp in sorted(node.inputs, key=_node_sort_key):
            visit(inp)
        order.append(node)

    for node in sorted(nodes, key=_node_sort_key):
        visit(node)

    return order
