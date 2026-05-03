"""
Operator approval — controls the candidate → approved → active lifecycle.

Approval flow for new runtime operators:
  governed_register(cdl_op, version, metadata) → "candidate"
  approve_operator(operator_key)               → "active"

Bootstrap flow for pre-approved system operators (domain modules):
  govern_all_registered()   → registers all CDL-registry operators as "active"

Rules:
- No auto-approval of runtime-registered operators.
- Only "active" operators are executable.
- Bootstrap operators are pre-approved by system designers (domain module authors).
- Approval is idempotent: approving an already-active operator is a no-op.
"""
from __future__ import annotations

from typing import Dict, Optional

from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.types.base import TypeSignature
from l_cdea.operator_governance.registry import (
    GovernedOperator, GovernedRegistry,
    OperatorNotFoundError, OperatorDuplicateError,
)
from l_cdea.operator_governance.validator import validate_operator, assert_valid
from l_cdea.operator_governance.deduplication import detect_duplicate
from l_cdea.operator_governance.versioning import check_version_evolution, assert_valid_version
from l_cdea.operator_governance.audit import AuditLog


def governed_register(
    cdl_op: CDLOperator,
    version: str = "1.0",
    metadata: Optional[Dict] = None,
) -> GovernedOperator:
    """
    Register a new operator through the full governance pipeline.

    Status starts as "candidate". Call approve_operator(key) to activate.

    Raises:
        OperatorValidationError — if validation fails
        OperatorDuplicateError  — if a duplicate is detected
        OperatorVersionError    — if version evolution rules are violated
    """
    assert_valid_version(version)
    domain, name = _split_name(cdl_op.name)
    meta = dict(metadata) if metadata else {}

    op = GovernedOperator(
        name=name,
        domain=domain,
        version=version,
        signature=cdl_op.signature,
        implementation=cdl_op.transform,
        metadata=meta,
        status="candidate",
    )

    key = op.operator_key

    # Validate
    errors = validate_operator(op)
    if errors:
        AuditLog.record(key, version, "rejected",
                        validation_passed=False,
                        notes={"errors": errors})
        from l_cdea.operator_governance.registry import OperatorValidationError
        raise OperatorValidationError(
            f"Operator '{key}' failed validation:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    # Deduplication
    conflict = detect_duplicate(op)
    if conflict is not None:
        AuditLog.record(key, version, "rejected",
                        validation_passed=True, duplicate_detected=True,
                        notes={"conflict": conflict})
        raise OperatorDuplicateError(
            f"Operator '{key}' conflicts with '{conflict}'."
        )

    # Version evolution
    check_version_evolution(op)

    # Register as candidate
    GovernedRegistry.register(op)
    AuditLog.record(key, version, "registered",
                    validation_passed=True, duplicate_detected=False, approved=False)
    return op


def approve_operator(operator_key: str) -> GovernedOperator:
    """
    Promote a "candidate" operator to "active".
    Idempotent if already active.

    Raises OperatorNotFoundError if the key is not in the governed registry.
    """
    op = GovernedRegistry.get(operator_key)
    if op.status == "active":
        return op  # already active — idempotent
    GovernedRegistry.update_status(operator_key, "active")
    AuditLog.record(operator_key, op.version, "approved",
                    validation_passed=True, duplicate_detected=False, approved=True)
    return GovernedRegistry.get(operator_key)


def deprecate_operator(operator_key: str) -> None:
    """Mark an operator as deprecated (no longer executable)."""
    op = GovernedRegistry.get(operator_key)
    GovernedRegistry.update_status(operator_key, "deprecated")
    AuditLog.record(operator_key, op.version, "deprecated",
                    validation_passed=True, approved=False)


def _bootstrap_one(cdl_op: CDLOperator, version: str = "1.0") -> None:
    """
    Register a pre-approved system operator as active without candidate flow.
    Used by govern_all_registered() — not for runtime use.
    Idempotent: silently skips already-governed operators.
    """
    domain, name = _split_name(cdl_op.name)
    key = f"{domain}.{name}@{version}"

    if GovernedRegistry.has(key):
        return  # already governed — idempotent

    op = GovernedOperator(
        name=name,
        domain=domain,
        version=version,
        signature=cdl_op.signature,
        implementation=cdl_op.transform,
        metadata={"deterministic": True, "bootstrap": True},
        status="active",
    )

    errors = validate_operator(op)
    if errors:
        AuditLog.record(key, version, "rejected",
                        validation_passed=False,
                        notes={"errors": errors, "bootstrap": True})
        return  # bootstrap failures are logged but do not crash startup

    GovernedRegistry.register(op)
    AuditLog.record(key, version, "registered",
                    validation_passed=True, duplicate_detected=False,
                    approved=True, notes={"bootstrap": True})


def govern_all_registered(version: str = "1.0") -> int:
    """
    Bootstrap governance for all operators already in the CDL OperatorRegistry.

    Iterates OperatorRegistry.list(), creates GovernedOperator(status="active")
    for each, validates, and registers. Idempotent — safe to call multiple times.

    Returns the number of operators newly governed (0 if already up-to-date).
    """
    from l_cdea.core.cdl.registry import OperatorRegistry

    count = 0
    for op_name in OperatorRegistry.list():
        cdl_op = OperatorRegistry.get(op_name)
        domain, name = _split_name(op_name)
        key = f"{domain}.{name}@{version}"
        if GovernedRegistry.has(key):
            continue
        _bootstrap_one(cdl_op, version)
        count += 1
    return count


def _split_name(full_name: str):
    """Split "domain.NAME" → (domain, NAME). Falls back to ("core", full_name)."""
    if "." in full_name:
        domain, _, name = full_name.partition(".")
        return domain, name
    return "core", full_name
