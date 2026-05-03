"""
GET_RELATIONSHIPS CDL operator.

discourse.GET_RELATIONSHIPS(term: Entity, relation_type: Entity) → Entity

Execution:
  1. Normalize term and relation_type.
  2. Look up matching edges in DiscourseState.
  3. Return formatted list of related terms.
  4. Fallback: relationships_of(term, relation_type) — never crashes.

Governance: registered as active via register_governed_operators().
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError


def _get_relationships_impl(term_tv: TypedValue, relation_type_tv: TypedValue) -> TypedValue:
    """CDL operator transform — queries the active DiscourseState."""
    from l_cdea.discourse.relationship_query.lookup import lookup_relationships
    from l_cdea.discourse.relationship_query.normalization import normalize_term

    term = str(term_tv.value)
    relation_type = str(relation_type_tv.value)

    # Access global state (same pattern as GET_DEFINITION)
    try:
        from l_cdea import run as _run_mod
        state = _run_mod._state
    except Exception:
        state = None

    if state is not None:
        result, _ = lookup_relationships(term, relation_type, state)
        if result.hit and result.values:
            lines = [f"{normalize_term(term)} {relation_type}:"]
            for v in result.values:
                lines.append(f"  - {v}")
            return TypedValue("\n".join(lines), SemanticType.ENTITY)

    return TypedValue(
        f"relationships_of({normalize_term(term)}, {relation_type})",
        SemanticType.ENTITY,
    )


E = SemanticType.ENTITY

GET_RELATIONSHIPS = CDLOperator(
    name="discourse.GET_RELATIONSHIPS",
    signature=TypeSignature(input_types=[E, E], output_type=E),
    transform=_get_relationships_impl,
)

ALL_RELATIONSHIP_OPERATORS = [GET_RELATIONSHIPS]


def register_discourse_operators() -> None:
    """Register GET_RELATIONSHIPS in the CDL OperatorRegistry. Idempotent."""
    for op in ALL_RELATIONSHIP_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators() -> None:
    """Bootstrap relationship operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
