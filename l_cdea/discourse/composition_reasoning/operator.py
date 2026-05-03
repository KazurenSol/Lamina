"""
COMPOSE_RELATIONSHIPS CDL operator.

discourse.COMPOSE_RELATIONSHIPS(term: Entity, relation_type: Entity, max_depth: Entity) → Entity

Executes composition reasoning: BFS traversal + direct/indirect separation.
Governance: registered as active via register_governed_operators().
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError


def _compose_relationships_impl(
    term_tv: TypedValue,
    relation_type_tv: TypedValue,
    max_depth_tv: TypedValue,
) -> TypedValue:
    from l_cdea.discourse.composition_reasoning.composer import compose
    from l_cdea.discourse.relationship_query.normalization import normalize_term

    term = str(term_tv.value)
    relation_type = str(relation_type_tv.value)
    try:
        max_depth = int(str(max_depth_tv.value))
    except (ValueError, TypeError):
        max_depth = 3

    try:
        from l_cdea import run as _run_mod
        state = _run_mod._state
    except Exception:
        state = None

    if state is not None:
        result, _ = compose(term, relation_type, state, max_depth)
        if not result.fallback_used:
            lines = [f"{normalize_term(term)} dependencies:"]
            if result.direct:
                lines.append("Direct:")
                for cr in result.direct:
                    lines.append(f"  - {cr.target}")
            if result.indirect:
                lines.append("Indirect:")
                for cr in result.indirect:
                    lines.append(f"  - {cr.target}")
            return TypedValue("\n".join(lines), SemanticType.ENTITY)

    return TypedValue(
        f"compose_of({normalize_term(term)}, {relation_type})",
        SemanticType.ENTITY,
    )


E = SemanticType.ENTITY

COMPOSE_RELATIONSHIPS = CDLOperator(
    name="discourse.COMPOSE_RELATIONSHIPS",
    signature=TypeSignature(input_types=[E, E, E], output_type=E),
    transform=_compose_relationships_impl,
)

ALL_COMPOSITION_OPERATORS = [COMPOSE_RELATIONSHIPS]


def register_discourse_operators() -> None:
    for op in ALL_COMPOSITION_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators() -> None:
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
