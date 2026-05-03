"""
GET_DEFINITION CDL operator.

discourse.GET_DEFINITION(term: Entity) → Entity

Execution:
  1. Normalize term
  2. Search definition store
  3. Return stored text
  4. Fallback: definition_of(term) — never crashes

Governance: registered as active via register_governed_operators().
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError


def _get_definition_impl(term_tv: TypedValue) -> TypedValue:
    """CDL operator transform — uses module-level definition store."""
    from l_cdea.discourse.definition_retrieval.lookup import lookup_definition
    from l_cdea.discourse.definition_retrieval.normalization import normalize_term

    term = str(term_tv.value)
    result = lookup_definition(term, state=None)
    if result.hit and result.definition_text:
        return TypedValue(result.definition_text, SemanticType.ENTITY)
    return TypedValue(f"definition_of({normalize_term(term)})", SemanticType.ENTITY)


E = SemanticType.ENTITY

GET_DEFINITION = CDLOperator(
    name="discourse.GET_DEFINITION",
    signature=TypeSignature(input_types=[E], output_type=E),
    transform=_get_definition_impl,
)

ALL_DISCOURSE_OPERATORS = [GET_DEFINITION]


def register_discourse_operators() -> None:
    """Register discourse operators in the CDL OperatorRegistry. Idempotent."""
    for op in ALL_DISCOURSE_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators() -> None:
    """Bootstrap discourse operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
