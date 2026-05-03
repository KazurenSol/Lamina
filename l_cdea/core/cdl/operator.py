from dataclasses import dataclass
from typing import Callable
from l_cdea.core.types.base import TypeSignature, TypedValue
from l_cdea.core.types.constraints import validate_signature
from .exceptions import TypeMismatchError


@dataclass(frozen=True)
class CDLOperator:
    """Deterministic semantic transformation function."""

    name: str
    signature: TypeSignature
    transform: Callable[..., TypedValue]

    def __post_init__(self):
        validate_signature(self.signature)

    def execute(self, *args: TypedValue) -> TypedValue:
        if len(args) != len(self.signature.input_types):
            raise TypeMismatchError(
                f"Operator '{self.name}' expects {len(self.signature.input_types)} "
                f"inputs, got {len(args)}"
            )
        for i, (arg, expected) in enumerate(zip(args, self.signature.input_types)):
            if arg.type != expected:
                raise TypeMismatchError(
                    f"Operator '{self.name}' input[{i}]: expected {expected}, got {arg.type}"
                )
        result = self.transform(*args)
        if result.type != self.signature.output_type:
            raise TypeMismatchError(
                f"Operator '{self.name}' output: expected {self.signature.output_type}, "
                f"got {result.type}"
            )
        return result
