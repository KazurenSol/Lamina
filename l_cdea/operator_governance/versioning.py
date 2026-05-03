"""
Operator versioning — semantic version enforcement and evolution rules.

Version format: MAJOR.MINOR  (e.g. "1.0", "1.1", "2.0")

Increment rules:
  MAJOR — breaking change in TypeSignature (input_types or output_type changed)
  MINOR — internal improvement, TypeSignature unchanged

Rules:
  - Same name+domain + same version → error (use deduplication path)
  - Same name+domain + different version → must coexist, must not override
  - Versions MUST follow MAJOR.MINOR format
  - Breaking TypeSignature change without MAJOR bump → rejected
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from l_cdea.core.types.base import TypeSignature
from l_cdea.operator_governance.registry import (
    GovernedOperator, GovernedRegistry, OperatorVersionError,
)

_VERSION_RE = re.compile(r"^\d+\.\d+$")


def validate_version(version: str) -> bool:
    """Return True if version matches MAJOR.MINOR format."""
    return bool(_VERSION_RE.match(version))


def parse_version(version: str) -> Tuple[int, int]:
    parts = version.split(".")
    return int(parts[0]), int(parts[1])


def is_breaking_change(old_sig: TypeSignature, new_sig: TypeSignature) -> bool:
    """True if input_types or output_type changed — requires MAJOR bump."""
    return (
        old_sig.input_types != new_sig.input_types
        or old_sig.output_type != new_sig.output_type
    )


def requires_major_bump(old_op: GovernedOperator, new_op: GovernedOperator) -> bool:
    """True if the change between old and new versions requires a MAJOR bump."""
    return is_breaking_change(old_op.signature, new_op.signature)


def assert_valid_version(version: str) -> None:
    if not validate_version(version):
        raise OperatorVersionError(
            f"Version '{version}' does not follow MAJOR.MINOR format (e.g. '1.0')."
        )


def check_version_evolution(op: GovernedOperator) -> None:
    """
    Validate version evolution rules against already-registered versions
    of the same operator (same domain + name).

    Raises OperatorVersionError if:
    - Version format invalid
    - Breaking TypeSignature change without MAJOR bump
    """
    assert_valid_version(op.version)
    new_major, _ = parse_version(op.version)

    existing_keys = [
        k for k in GovernedRegistry.list_operators()
        if GovernedRegistry.get(k).domain == op.domain
        and GovernedRegistry.get(k).name == op.name
    ]

    for key in existing_keys:
        existing = GovernedRegistry.get(key)
        old_major, _ = parse_version(existing.version)

        if is_breaking_change(existing.signature, op.signature):
            if new_major <= old_major:
                raise OperatorVersionError(
                    f"Operator '{op.operator_key}' changes TypeSignature relative to "
                    f"'{key}' but does not increment MAJOR version "
                    f"({existing.version} → {op.version}). "
                    "Breaking changes require a MAJOR bump."
                )
