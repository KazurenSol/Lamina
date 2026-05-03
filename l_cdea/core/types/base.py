from dataclasses import dataclass
from enum import Enum
from typing import Any, Tuple


class SemanticType(Enum):
    ENTITY = "Entity"
    EVENT = "Event"
    STATE = "State"
    PROCESS = "Process"
    RELATION = "Relation"
    CONSTRAINT = "Constraint"
    ABSTRACTION = "Abstraction"


@dataclass(frozen=True)
class TypedValue:
    """Atomic typed semantic unit. Used across CDL, DiscourseState, and execution graphs."""
    value: Any
    type: SemanticType


@dataclass(frozen=True)
class TypeSignature:
    """Input/output contract for CDL operators."""
    input_types: Tuple[SemanticType, ...]
    output_type: SemanticType
