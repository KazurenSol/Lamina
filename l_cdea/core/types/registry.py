from typing import FrozenSet
from .base import SemanticType


class TypeRegistry:
    """Single source of truth for allowed semantic types. Enforces system-wide type validity."""

    _allowed_types: FrozenSet[SemanticType] = frozenset(SemanticType)

    @classmethod
    def validate(cls, t: SemanticType) -> bool:
        return t in cls._allowed_types

    @classmethod
    def list_types(cls) -> list:
        return list(cls._allowed_types)
