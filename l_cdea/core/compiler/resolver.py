from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple

from l_cdea.core.types.base import SemanticType
from l_cdea.core.parser.presemantic import PreSemanticFrame
from .exceptions import TypeResolutionError

# Each frame_type maps to one or more (input_types, output_type) interpretations.
# Multiple entries per frame_type reflect genuine semantic ambiguity — all are emitted.
_FRAME_TYPE_MAP: Dict[str, List[Tuple[Tuple[SemanticType, ...], SemanticType]]] = {
    "PROPOSITION": [
        ((SemanticType.ENTITY, SemanticType.RELATION), SemanticType.STATE),
        ((SemanticType.ENTITY, SemanticType.PROCESS), SemanticType.EVENT),
    ],
    "PREDICATION": [
        ((SemanticType.ENTITY, SemanticType.CONSTRAINT), SemanticType.STATE),
    ],
    "ENTITY_RELATION": [
        ((SemanticType.ENTITY, SemanticType.RELATION, SemanticType.ENTITY), SemanticType.RELATION),
    ],
    "EVENT": [
        ((SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.ENTITY), SemanticType.EVENT),
        ((SemanticType.ENTITY, SemanticType.PROCESS), SemanticType.EVENT),
    ],
    "NOMINAL": [
        ((SemanticType.ENTITY,), SemanticType.ENTITY),
        ((SemanticType.ABSTRACTION,), SemanticType.ABSTRACTION),
    ],
    "GENERIC": [
        ((SemanticType.ABSTRACTION,), SemanticType.ABSTRACTION),
    ],
    "MULTI_CLAUSE": [
        ((SemanticType.RELATION, SemanticType.RELATION), SemanticType.ABSTRACTION),
        ((SemanticType.EVENT, SemanticType.EVENT), SemanticType.ABSTRACTION),
    ],
}


@dataclass(frozen=True)
class TypedInterpretation:
    """
    A candidate typed reading of a PreSemanticFrame.
    Frozen + hashable so it can live in a frozenset.
    Multiple interpretations per frame are normal — MECP prunes later.
    """
    frame: PreSemanticFrame
    input_types: Tuple[SemanticType, ...]
    output_type: SemanticType


TypedInterpretationSet = FrozenSet[TypedInterpretation]


def resolve(frames: FrozenSet[PreSemanticFrame]) -> TypedInterpretationSet:
    """
    Map each PreSemanticFrame to all valid typed interpretations.
    Produces the full candidate space. No pruning or ranking here.
    """
    interpretations: set[TypedInterpretation] = set()
    for frame in frames:
        mappings = _FRAME_TYPE_MAP.get(frame.frame_type)
        if mappings is None:
            raise TypeResolutionError(f"No type mappings for frame_type '{frame.frame_type}'")
        for input_types, output_type in mappings:
            interpretations.add(TypedInterpretation(
                frame=frame,
                input_types=input_types,
                output_type=output_type,
            ))
    if not interpretations:
        raise TypeResolutionError("Type resolution produced no interpretations")
    return frozenset(interpretations)
