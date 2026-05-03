"""
GET_RELATIONSHIP_CLOSURE CDL operator.

discourse.GET_RELATIONSHIP_CLOSURE(term: Entity, relation_type: Entity, max_depth: Entity) → Entity

Execution:
  1. Normalize term and relation_type.
  2. Parse max_depth (default 3).
  3. Call compute_closure.
  4. Return formatted closure string.
  5. Fallback: closure_of(term, relation_type) — never crashes.

Governance: registered as active via register_governed_operators().
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError


def _get_relationship_closure_impl(
    term_tv: TypedValue,
    relation_type_tv: TypedValue,
    max_depth_tv: TypedValue,
) -> TypedValue:
    from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
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
        result, _ = compute_closure(term, relation_type, state, max_depth)
        if not result.fallback_used and result.paths:
            lines = [f"{normalize_term(term)} ultimately {relation_type}:"]
            for p in result.paths:
                lines.append(f"  - {p.target}")
                lines.append(f"    path: {' → '.join(p.path)}")
            return TypedValue("\n".join(lines), SemanticType.ENTITY)

    return TypedValue(
        f"closure_of({normalize_term(term)}, {relation_type})",
        SemanticType.ENTITY,
    )


E = SemanticType.ENTITY

GET_RELATIONSHIP_CLOSURE = CDLOperator(
    name="discourse.GET_RELATIONSHIP_CLOSURE",
    signature=TypeSignature(input_types=[E, E, E], output_type=E),
    transform=_get_relationship_closure_impl,
)

ALL_MULTI_HOP_OPERATORS = [GET_RELATIONSHIP_CLOSURE]


def register_discourse_operators() -> None:
    for op in ALL_MULTI_HOP_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators() -> None:
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
