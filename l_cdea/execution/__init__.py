from l_cdea.control.mecp import MECPResult
from .engine import ExecutionBundle, ExecutionResultSet, execute_graphs
from .evaluator import EvaluatedNode, evaluate_node
from .resolver import ResolvedExecutionOrder, resolve_order
from .runtime import ExecutionContext, GraphID, NodeID, make_context
from .exceptions import (
    ExecutionError,
    RuntimeEvaluationError,
    ResolutionError,
    ContextIsolationError,
    MECPOrderViolationError,
)


def run_execution(mecp_result: MECPResult) -> ExecutionBundle:
    """
    Entry point for the execution layer.
    Executes the MECP-selected graph subset in MECP order.
    Returns an ExecutionBundle — no side effects, no Discourse writes.
    """
    return execute_graphs(mecp_result)


__all__ = [
    "run_execution",
    "ExecutionBundle",
    "ExecutionResultSet",
    "EvaluatedNode",
    "ResolvedExecutionOrder",
    "ExecutionContext",
    "GraphID",
    "NodeID",
    "ExecutionError",
    "RuntimeEvaluationError",
    "ResolutionError",
    "ContextIsolationError",
    "MECPOrderViolationError",
]
