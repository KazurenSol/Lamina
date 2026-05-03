"""
Minimal CDLGraph construction from a resolved CDLOperator and hydrated slot values.

Rules:
- No execution
- No MECP
- No mutation of inputs
- Deterministic node ordering: V1 alphabetical, V2 PatternRule.arg_order
- Returns a valid CDLGraph ready to pass to the execution layer
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from l_cdea.core.types.base import TypedValue
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.node import CDLNode
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.planner.plan import PlanningError
from l_cdea.core.planner.operator_resolver import slot_key_order


def build_graph(
    operator: CDLOperator,
    hydrated_slots: Dict[str, TypedValue],
    arg_order: Tuple[str, ...] = (),
) -> Tuple[Optional[CDLGraph], Optional[PlanningError]]:
    """
    Build a minimal CDLGraph:
      - One leaf node per slot (operator=None, value=TypedValue)
      - One operator node consuming all leaf nodes as inputs
    Slot order: slot_key_order(hydrated_slots, arg_order) — V1 alphabetical,
    V2 explicit PatternRule.arg_order.
    Returns (graph, None) on success, (None, PlanningError) on failure.
    """
    try:
        # Create input leaf nodes in deterministic slot order
        keys = slot_key_order(hydrated_slots, arg_order)
        input_nodes: List[CDLNode] = [
            CDLNode(operator=None, value=hydrated_slots[k])
            for k in keys
        ]

        # Create the operator node
        op_node = CDLNode(operator=operator, inputs=input_nodes)

        # Assemble graph: leaves first, operator node last (valid topological order)
        graph = CDLGraph()
        for node in input_nodes:
            graph.add_node(node)
        graph.add_node(op_node)

        return graph, None

    except Exception as exc:
        return None, PlanningError(
            code=PlanningError.GRAPH_BUILD_FAILED,
            message=f"Graph construction failed: {exc}",
            details={"operator": operator.name, "slots": list(hydrated_slots.keys())},
        )


class ExecutionGovernanceError(Exception):
    """Raised when a graph contains an operator not registered as active in governance."""
    def __init__(self, message: str, operator_name: str = ""):
        super().__init__(message)
        self.operator_name = operator_name


def validate_graph_operators_are_governed(graph: CDLGraph) -> None:
    """
    Validate that every operator node in the graph maps to an active GovernedOperator.
    Input/value-only nodes (operator=None) are exempt.

    In permissive mode: logs a warning but does not raise.
    In strict mode: raises ExecutionGovernanceError for any ungoverned or non-active operator.
    Raises ExecutionGovernanceError for any governed-but-not-active operator regardless of mode.
    """
    try:
        from l_cdea.operator_governance.registry import GovernedRegistry
        from l_cdea.operator_governance.config import is_strict_mode
    except ImportError:
        return  # governance module not available — passthrough

    strict = is_strict_mode()

    for node in graph.nodes:
        if node.operator is None:
            continue  # leaf/value node — exempt
        op_name = node.operator.name  # e.g. "math.ADD"
        status = GovernedRegistry.get_status(op_name)

        if status == "active":
            continue

        if status is None:
            # Ungoverned
            if strict:
                raise ExecutionGovernanceError(
                    f"Operator '{op_name}' in execution graph is not governed. "
                    "Strict governance mode requires all operators to be active governed operators.",
                    operator_name=op_name,
                )
            # Permissive: continue (ungoverned pass-through)
        else:
            # Governed but not active (candidate or deprecated) — always reject
            raise ExecutionGovernanceError(
                f"Operator '{op_name}' in execution graph has status='{status}'. "
                "Only active governed operators may execute.",
                operator_name=op_name,
            )


def execute_plan_graph(graph: CDLGraph) -> Optional[TypedValue]:
    """
    Execute the minimal plan graph and return the operator node's result.
    The operator node is always the last node (topological order).
    Returns None if execution produces no result.
    Raises ExecutionGovernanceError if any operator node is not active and governed.
    """
    validate_graph_operators_are_governed(graph)
    graph.execute()
    # The last node in the graph is always the operator node
    op_node = graph.nodes[-1]
    return op_node.value if op_node.is_resolved() else None
