"""
Operator validator — enforces correctness before governance registration.

All checks are structural (no execution of the operator).
Failure returns a list of error strings; empty list = valid.
assert_valid() raises OperatorValidationError if invalid.
"""
from __future__ import annotations

from typing import List

from l_cdea.operator_governance.registry import GovernedOperator, OperatorValidationError


def validate_operator(op: GovernedOperator) -> List[str]:
    """
    Validate a GovernedOperator before registration.

    Checks:
    1. TypeSignature present and valid
    2. input_types length > 0
    3. output_type defined
    4. implementation is callable
    5. determinism declared in metadata (metadata["deterministic"] must be True)
    6. no external_deps declared (metadata.get("external_deps", False) must be False)
    7. name, domain, version non-empty
    """
    from l_cdea.core.types.base import SemanticType

    errors: List[str] = []

    if not op.name:
        errors.append("name must be non-empty")

    if not op.domain:
        errors.append("domain must be non-empty")

    if not op.version:
        errors.append("version must be non-empty")

    # TypeSignature
    if op.signature is None:
        errors.append("signature must be defined")
    else:
        if not op.signature.input_types:
            errors.append("signature.input_types must be non-empty (length > 0)")
        else:
            for i, t in enumerate(op.signature.input_types):
                if not isinstance(t, SemanticType):
                    errors.append(f"signature.input_types[{i}] is not a SemanticType")

        if op.signature.output_type is None:
            errors.append("signature.output_type must be defined")
        elif not isinstance(op.signature.output_type, SemanticType):
            errors.append("signature.output_type is not a SemanticType")

    # Implementation
    if not callable(op.implementation):
        errors.append("implementation must be callable")

    # Determinism (declared in metadata)
    if not op.metadata.get("deterministic", True):
        errors.append(
            "metadata['deterministic'] must be True — "
            "non-deterministic operators are not allowed in V1"
        )

    # External dependencies
    if op.metadata.get("external_deps", False):
        errors.append(
            "metadata['external_deps'] must be absent or False — "
            "operators MUST NOT call external services in V1"
        )

    return errors


def assert_valid(op: GovernedOperator) -> None:
    errors = validate_operator(op)
    if errors:
        raise OperatorValidationError(
            f"Operator '{op.operator_key}' failed validation:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
