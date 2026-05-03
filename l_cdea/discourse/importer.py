from __future__ import annotations

from typing import Any, Dict, List, Optional

from l_cdea.core.types.base import SemanticType, TypedValue
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.cdl.node import CDLNode
from l_cdea.execution.engine import ExecutionBundle
from .node import DiscourseNode, BASE_SALIENCE, REINFORCEMENT, make_node_id
from .edge import DiscourseEdge
from .state import DiscourseState
from .salience import apply_decay
from .temporal import TemporalEvent, record_event, advance_index
from .memory_graph import add_node, add_edge, merge_duplicate
from .exceptions import DiscourseImportError
from .provenance.model import Provenance, make_trace_id
from .provenance.merge import merge_provenance

# ── Provenance factory ────────────────────────────────────────────────────────

def _make_node_provenance(node_value: Any, operator_name: str, timestamp_index: int) -> Provenance:
    """
    Build provenance for a node being imported.

    Dataset-backed: if a lookup trace matches the value, use dataset provenance.
    Otherwise: execution provenance with the operator name.
    """
    try:
        from l_cdea.data.lookup import get_all_lookup_traces
        for trace in get_all_lookup_traces():
            if trace.hit and trace.returned_value == node_value:
                source_id = trace.provenance.get("source_id", trace.dataset_name)
                return Provenance(
                    source_id=source_id,
                    source_type="dataset",
                    extraction_method="dataset_lookup",
                    confidence=1.0,
                    trace_id=make_trace_id(source_id, "dataset_lookup", timestamp_index),
                    timestamp_index=timestamp_index,
                )
    except Exception:
        pass

    return Provenance(
        source_id=operator_name or "import_bundle",
        source_type="execution",
        extraction_method=operator_name or "import_bundle",
        confidence=1.0,
        trace_id=make_trace_id(operator_name or "import_bundle", "execution", timestamp_index),
        timestamp_index=timestamp_index,
    )


# Types worth tracking individually in discourse
_TRACKED_TYPES = frozenset({
    SemanticType.ENTITY,
    SemanticType.RELATION,
    SemanticType.EVENT,
    SemanticType.STATE,
    SemanticType.PROCESS,
})


def import_bundle(bundle: ExecutionBundle, state: DiscourseState) -> tuple[
    list[DiscourseNode], list[DiscourseNode], list[DiscourseEdge], list[TemporalEvent]
]:
    """
    Import executed results into DiscourseState.
    Only successful graph outputs enter as semantic truth.
    Failed graph outputs are recorded as metadata only (no semantic nodes created).
    All updates happen after full execution — no streaming writes.
    """
    added_nodes: list[DiscourseNode] = []
    reinforced_nodes: list[DiscourseNode] = []
    added_edges: list[DiscourseEdge] = []
    temporal_events: list[TemporalEvent] = []

    for graph in bundle.resolved_graphs:
        root = _find_root(graph)
        root_val = bundle.node_outputs.get(id(root)) if root else None
        if root_val is None and root:
            root_val = root.value  # pre-set leaf fallback

        if root_val is None:
            continue

        # Determine operator name for provenance (root operator node)
        op_name = ""
        try:
            if root is not None and root.operator:
                op_name = root.operator.name
        except Exception:
            pass

        # Root discourse node (the semantic result)
        root_id = make_node_id(root_val.type, root_val.value)
        root_prov = _make_node_provenance(root_val.value, op_name, state.temporal_index)
        if root_id in state.nodes:
            merge_duplicate(state, root_id, REINFORCEMENT)
            existing_node = state.nodes[root_id]
            merge_result = merge_provenance(
                existing_node.value, existing_node.provenance,
                root_val.value, root_prov,
            )
            existing_node.provenance = merge_result.merged_provenance
            reinforced_nodes.append(existing_node)
            record_event(temporal_events, state.temporal_index, "reinforce_node", [root_id])
        else:
            rn = DiscourseNode(
                id=root_id, semantic_type=root_val.type, value=root_val.value,
                salience=BASE_SALIENCE, created_at=state.temporal_index,
                updated_at=state.temporal_index,
                provenance=(root_prov,),
            )
            add_node(state, rn)
            added_nodes.append(rn)
            record_event(temporal_events, state.temporal_index, "add_node", [root_id])

        # Leaf nodes — track entities and relations individually
        for node in graph.nodes:
            if node.inputs:
                continue  # operator node, not a leaf
            leaf_val = bundle.node_outputs.get(id(node)) or node.value
            if leaf_val is None or leaf_val.type not in _TRACKED_TYPES:
                continue
            leaf_id = make_node_id(leaf_val.type, leaf_val.value)
            if leaf_id == root_id:
                continue  # already handled
            leaf_prov = _make_node_provenance(leaf_val.value, op_name, state.temporal_index)
            if leaf_id in state.nodes:
                merge_duplicate(state, leaf_id, REINFORCEMENT * 0.5)
                existing_leaf = state.nodes[leaf_id]
                merge_result = merge_provenance(
                    existing_leaf.value, existing_leaf.provenance,
                    leaf_val.value, leaf_prov,
                )
                existing_leaf.provenance = merge_result.merged_provenance
                reinforced_nodes.append(existing_leaf)
            else:
                ln = DiscourseNode(
                    id=leaf_id, semantic_type=leaf_val.type, value=leaf_val.value,
                    salience=BASE_SALIENCE * 0.8, created_at=state.temporal_index,
                    updated_at=state.temporal_index,
                    provenance=(leaf_prov,),
                )
                add_node(state, ln)
                added_nodes.append(ln)

            # Edge: leaf → root (typed by leaf semantic type)
            edge = DiscourseEdge(
                source_id=leaf_id, target_id=root_id,
                relation_type=leaf_val.type.value, salience=BASE_SALIENCE,
            )
            if add_edge(state, edge):
                added_edges.append(edge)

    # Record failure metadata — no semantic nodes
    for graph_id, errors in bundle.failures.items():
        if errors:
            record_event(temporal_events, state.temporal_index, "failure", [],
                         metadata=f"graph {graph_id}: {errors[0]}")

    apply_decay(state)
    advance_index(state)
    return added_nodes, reinforced_nodes, added_edges, temporal_events


def _find_root(graph: CDLGraph) -> Optional[CDLNode]:
    """Root = node not used as input by any other node."""
    consumed: set[int] = set()
    for n in graph.nodes:
        for inp in n.inputs:
            consumed.add(id(inp))
    roots = [n for n in graph.nodes if id(n) not in consumed]
    return roots[-1] if roots else None
