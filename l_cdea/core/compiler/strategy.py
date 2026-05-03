from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple

from l_cdea.core.types.base import SemanticType
from .binding import OperatorBinding, OperatorBindingSet


@dataclass(frozen=True)
class InterpretationStrategy:
    """
    A structural grouping of operator bindings under a named disambiguation strategy.
    No scoring, no ranking — strategies describe shape, not priority.
    MECP selects among strategies downstream.
    """
    strategy_type: str
    bindings: Tuple[OperatorBinding, ...]


InterpretationStrategySet = FrozenSet[InterpretationStrategy]


def stratify(bindings: OperatorBindingSet) -> InterpretationStrategySet:
    """
    Group operator bindings into structural disambiguation strategies.
    All bindings must appear in at least one strategy — none are dropped here.
    """
    strategies: set[InterpretationStrategy] = set()

    # PARALLEL — bindings that share the same output type run in parallel branches
    by_output: dict[SemanticType, list[OperatorBinding]] = {}
    for b in bindings:
        key = b.interpretation.output_type
        by_output.setdefault(key, []).append(b)

    for output_type, group in by_output.items():
        if len(group) >= 2:
            strategies.add(InterpretationStrategy(
                strategy_type="PARALLEL",
                bindings=tuple(sorted(group, key=lambda b: b.operator.name)),
            ))

    # MIRRORED — bindings with identical input type patterns but different operators
    by_input_pattern: dict[tuple, list[OperatorBinding]] = {}
    for b in bindings:
        key = b.interpretation.input_types
        by_input_pattern.setdefault(key, []).append(b)

    for pattern, group in by_input_pattern.items():
        ops = {b.operator.name for b in group}
        if len(ops) >= 2:
            strategies.add(InterpretationStrategy(
                strategy_type="MIRRORED",
                bindings=tuple(sorted(group, key=lambda b: b.operator.name)),
            ))

    # FALLBACK_GENERIC — bindings using structural generic operators (no registered match)
    generic_bindings = [b for b in bindings if b.operator.name.startswith("_generic_")]
    if generic_bindings:
        strategies.add(InterpretationStrategy(
            strategy_type="FALLBACK_GENERIC",
            bindings=tuple(sorted(generic_bindings, key=lambda b: b.operator.name)),
        ))

    # SINGLETON — any binding not captured by a multi-binding strategy gets its own
    covered: set[OperatorBinding] = set()
    for s in strategies:
        covered.update(s.bindings)
    for b in bindings:
        if b not in covered:
            strategies.add(InterpretationStrategy(
                strategy_type="SINGLETON",
                bindings=(b,),
            ))

    return frozenset(strategies)
