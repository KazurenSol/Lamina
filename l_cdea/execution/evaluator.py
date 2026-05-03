from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from l_cdea.core.cdl.node import CDLNode
from l_cdea.core.types.base import TypedValue
from .runtime import ExecutionContext
from .exceptions import RuntimeEvaluationError


@dataclass
class EvaluatedNode:
    """Result of evaluating a single CDLNode within an ExecutionContext."""
    node: CDLNode
    output: TypedValue
    success: bool
    error: Optional[RuntimeEvaluationError] = None


def evaluate_node(node: CDLNode, context: ExecutionContext) -> EvaluatedNode:
    """
    Execute one CDLNode within its isolated context.

    Leaf nodes (no inputs): return the pre-set TypedValue from the compiler.
    Operator nodes: collect resolved input values from context, invoke operator.

    Single-pass: each node is evaluated exactly once. Re-evaluation raises
    ContextIsolationError via context.store().
    TypeSignature is enforced by CDLOperator.execute() — not recomputed here.
    """
    node_id = id(node)

    if not node.inputs:
        # Leaf node — value must have been pre-set by the compiler
        if node.value is None:
            raise RuntimeEvaluationError(
                f"Leaf node for operator '{node.operator.name}' has no pre-set value"
            )
        context.store(node_id, node.value)
        return EvaluatedNode(node=node, output=node.value, success=True)

    # Operator node — collect input values from context
    input_values = []
    for i, inp in enumerate(node.inputs):
        val = context.get(id(inp))
        if val is None:
            raise RuntimeEvaluationError(
                f"Input [{i}] of operator '{node.operator.name}' not resolved — "
                f"dependency '{inp.operator.name}' must precede this node in execution order"
            )
        input_values.append(val)

    # Execute: CDLOperator.execute() enforces TypeSignature validation
    result = node.operator.execute(*input_values)
    # Write result back to the node's value field — this is the intended execution
    # contract. CDL structure (topology, operators, signatures) is not modified;
    # only the computed value slot is filled, which is why CDLNode.value exists.
    node.value = result
    context.store(node_id, result)
    return EvaluatedNode(node=node, output=result, success=True)
