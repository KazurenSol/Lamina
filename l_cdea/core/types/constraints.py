from .base import SemanticType, TypeSignature
from .registry import TypeRegistry


class TypeConstraintError(Exception):
    pass


def validate_signature(sig: TypeSignature) -> bool:
    """Ensures CDL operators obey strict type rules. Raises TypeConstraintError on violation."""
    for t in sig.input_types:
        if not isinstance(t, SemanticType):
            raise TypeConstraintError(f"Invalid input type: {t!r}")
        if not TypeRegistry.validate(t):
            raise TypeConstraintError(f"Unregistered input type: {t!r}")

    if not isinstance(sig.output_type, SemanticType):
        raise TypeConstraintError(f"Invalid output type: {sig.output_type!r}")
    if not TypeRegistry.validate(sig.output_type):
        raise TypeConstraintError(f"Unregistered output type: {sig.output_type!r}")

    return True
