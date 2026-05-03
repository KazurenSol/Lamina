from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import FrozenSet

from l_cdea.core.types.base import TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError
from .resolver import TypedInterpretation, TypedInterpretationSet
from .exceptions import BindingError


@dataclass(frozen=True)
class OperatorBinding:
    """Binds a typed interpretation to a concrete CDL operator."""
    interpretation: TypedInterpretation
    operator: CDLOperator


OperatorBindingSet = FrozenSet[OperatorBinding]


def bind(interpretations: TypedInterpretationSet) -> OperatorBindingSet:
    """
    Match each TypedInterpretation to a CDLOperator.
    Prefers registered operators; falls back to a structural generic operator.
    All valid interpretations produce a binding — none are dropped here.
    """
    bindings: set[OperatorBinding] = set()
    for interp in interpretations:
        sig = TypeSignature(input_types=interp.input_types, output_type=interp.output_type)
        op = _find_operator(sig)
        bindings.add(OperatorBinding(interpretation=interp, operator=op))
    if not bindings:
        raise BindingError("Binding produced no operator assignments")
    return frozenset(bindings)


def _find_operator(sig: TypeSignature) -> CDLOperator:
    """
    Return the first registered operator whose signature matches exactly,
    or fall back to a structural generic operator for that signature.
    """
    for name in OperatorRegistry.list():
        try:
            op = OperatorRegistry.get(name)
            if op.signature == sig:
                return op
        except InvalidOperatorError:
            continue
    return _generic_op(sig)


@lru_cache(maxsize=None)
def _generic_op(sig: TypeSignature) -> CDLOperator:
    """
    Structural placeholder operator for interpretations with no registered match.
    Cached by signature so the same TypeSignature always returns the same object
    (preserves determinism and operator identity across the graph).
    """
    output_type = sig.output_type

    def generic_transform(*args: TypedValue) -> TypedValue:
        return TypedValue(
            value=tuple(a.value for a in args) if args else None,
            type=output_type,
        )

    return CDLOperator(
        name=f"_generic_{output_type.value}_{len(sig.input_types)}in",
        signature=sig,
        transform=generic_transform,
    )
