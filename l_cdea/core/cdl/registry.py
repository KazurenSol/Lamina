from typing import Dict, List
from .operator import CDLOperator
from .exceptions import InvalidOperatorError


class OperatorRegistry:
    """Global registry for CDL operators. Immutable after system bootstrap."""

    _operators: Dict[str, CDLOperator] = {}

    @classmethod
    def register(cls, op: CDLOperator):
        if op.name in cls._operators:
            raise InvalidOperatorError(f"Operator '{op.name}' is already registered")
        cls._operators[op.name] = op

    @classmethod
    def get(cls, name: str) -> CDLOperator:
        if name not in cls._operators:
            raise InvalidOperatorError(f"Unknown operator: '{name}'")
        return cls._operators[name]

    @classmethod
    def list(cls) -> List[str]:
        return list(cls._operators.keys())
