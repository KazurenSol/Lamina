from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.types.base import TypedValue
from l_cdea.control.mecp import MECPResult
from .runtime import GraphID, NodeID, ExecutionContext, make_context
from .resolver import resolve_order
from .evaluator import EvaluatedNode, evaluate_node
from .exceptions import ExecutionError, RuntimeEvaluationError

ExecutionResultSet = List[EvaluatedNode]


@dataclass
class ExecutionBundle:
    """
    Complete output of the execution layer.
    Memory updates are deferred — this bundle is the input to the next pipeline stage.
    Failures are isolated: a failed graph does not affect others.
    """
    results: ExecutionResultSet
    resolved_graphs: List[CDLGraph]
    node_outputs: Dict[NodeID, TypedValue]
    failures: Dict[GraphID, List[ExecutionError]]
    success_flags: Dict[GraphID, bool]

    @property
    def success_count(self) -> int:
        return sum(1 for v in self.success_flags.values() if v)

    @property
    def failure_count(self) -> int:
        return sum(1 for v in self.success_flags.values() if not v)


def execute_graphs(mecp_result: MECPResult) -> ExecutionBundle:
    """
    Execute all graphs in the MECP-defined execution_subset order.

    MECP order is globally binding — graphs are processed in sequence,
    not reordered. Node order within each graph is topological only.
    Failures are caught per graph and recorded without halting the run.
    All memory updates deferred: this function returns a bundle, not side effects.
    """
    all_results: ExecutionResultSet = []
    resolved_graphs: List[CDLGraph] = []
    node_outputs: Dict[NodeID, TypedValue] = {}
    failures: Dict[GraphID, List[ExecutionError]] = {}
    success_flags: Dict[GraphID, bool] = {}

    for graph in mecp_result.execution_subset:   # MECP order — must not be changed
        graph_id = id(graph)
        try:
            context, evaluated = _execute_single_graph(graph)
            for en in evaluated:
                node_outputs[id(en.node)] = en.output
            all_results.extend(evaluated)
            resolved_graphs.append(graph)
            success_flags[graph_id] = True
            failures[graph_id] = []
        except ExecutionError as e:
            # Correction 3: failure is isolated — other graphs continue unaffected
            success_flags[graph_id] = False
            failures[graph_id] = [e]

    return ExecutionBundle(
        results=all_results,
        resolved_graphs=resolved_graphs,
        node_outputs=node_outputs,
        failures=failures,
        success_flags=success_flags,
    )


def _execute_single_graph(graph: CDLGraph) -> tuple[ExecutionContext, list[EvaluatedNode]]:
    """
    Execute one graph in isolation.
    Returns the context (for inspection) and the list of evaluated nodes.
    Single-pass: each node in topological order, evaluated exactly once.
    """
    order = resolve_order(graph)
    context = make_context(graph)
    evaluated: list[EvaluatedNode] = []

    for node in order.nodes:
        en = evaluate_node(node, context)
        evaluated.append(en)

    return context, evaluated
