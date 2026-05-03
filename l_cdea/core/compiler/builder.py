from __future__ import annotations

from typing import List

from l_cdea.core.types.base import SemanticType, TypedValue
from l_cdea.core.types.base import TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.node import CDLNode
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.parser.lexer import LexicalUnit, LexicalTag
from .binding import OperatorBinding, OperatorBindingSet
from .exceptions import GraphConstructionError


def build_graphs(bindings: OperatorBindingSet, units: List[LexicalUnit]) -> List[CDLGraph]:
    """
    Construct one CDLGraph per OperatorBinding.
    Graphs are inert — execution happens downstream after CAS and MECP.
    """
    if not bindings:
        raise GraphConstructionError("Cannot build graphs from empty binding set")
    content_units = [u for u in units if LexicalTag.WORD in u.tags or LexicalTag.NUMBER in u.tags]
    graphs = [_build_one(binding, content_units) for binding in sorted(bindings, key=_binding_key)]
    return graphs


def _build_one(binding: OperatorBinding, content_units: List[LexicalUnit]) -> CDLGraph:
    """
    Build a single CDLGraph for one OperatorBinding.
    Leaf nodes carry typed placeholder values aligned to input slots.
    Result node holds the bound operator consuming all leaves.
    """
    graph = CDLGraph()
    input_types = binding.interpretation.input_types
    leaf_nodes: List[CDLNode] = []

    for i, slot_type in enumerate(input_types):
        value = _slot_value(i, slot_type, content_units)
        terminal_op = _terminal_op(slot_type)
        leaf = CDLNode(operator=terminal_op, inputs=[], value=value)
        graph.add_node(leaf)
        leaf_nodes.append(leaf)

    result = CDLNode(operator=binding.operator, inputs=leaf_nodes)
    graph.add_node(result)
    return graph


def _slot_value(index: int, slot_type: SemanticType, units: List[LexicalUnit]) -> TypedValue:
    """Use the lexical form at position index if available; otherwise a positional placeholder."""
    if index < len(units):
        return TypedValue(value=units[index].form, type=slot_type)
    return TypedValue(value=f"<slot_{index}>", type=slot_type)


def _terminal_op(semantic_type: SemanticType) -> CDLOperator:
    """
    Identity/terminal operator for leaf nodes. Never executed — leaf nodes have
    no inputs, so CDLGraph.execute() skips them. Cached at module level for determinism.
    """
    return _TERMINAL_OPS[semantic_type]


def _binding_key(b: OperatorBinding) -> str:
    """Deterministic sort key so build_graphs output order is stable."""
    return f"{b.interpretation.frame.frame_type}:{b.operator.name}"


def _make_terminal(t: SemanticType) -> CDLOperator:
    sig = TypeSignature(input_types=(), output_type=t)

    def terminal() -> TypedValue:
        return TypedValue(value=None, type=t)

    return CDLOperator(name=f"_terminal_{t.value}", signature=sig, transform=terminal)


_TERMINAL_OPS: dict[SemanticType, CDLOperator] = {t: _make_terminal(t) for t in SemanticType}
