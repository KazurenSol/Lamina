"""
Operator deduplication — detect functionally equivalent operators before registration.

Duplicate detection checks:
1. Exact operator_key match (same name + domain + version) → always duplicate
2. Same TypeSignature + same implementation fingerprint (different version) → structural duplicate

On duplicate: registration is rejected unless the new entry is a distinct version
(same signature + explicit version increment = allowed version evolution, not duplicate).

A "structural duplicate" is two operators with:
- same domain + name
- same TypeSignature (input_types + output_type)
- same implementation fingerprint

If those match and the version is also the same → hard duplicate (error).
If those match but version differs → version evolution (allowed, but flagged in audit).
"""
from __future__ import annotations

import hashlib
import inspect
from typing import Optional

from l_cdea.operator_governance.registry import (
    GovernedOperator, GovernedRegistry, OperatorDuplicateError,
)


def implementation_fingerprint(op: GovernedOperator) -> str:
    """
    Compute a deterministic fingerprint for an operator's implementation.

    Strategy (in order of reliability):
    1. inspect.getsource() — exact source hash
    2. op.implementation.__code__.co_code — bytecode hash (lambdas/closures)
    3. str(op.implementation) — fallback string representation
    """
    try:
        src = inspect.getsource(op.implementation)
        return hashlib.sha256(src.encode()).hexdigest()[:16]
    except (OSError, TypeError):
        pass
    try:
        code = op.implementation.__code__.co_code
        return hashlib.sha256(code).hexdigest()[:16]
    except AttributeError:
        pass
    return hashlib.sha256(str(op.implementation).encode()).hexdigest()[:16]


def signature_fingerprint(op: GovernedOperator) -> str:
    sig = op.signature
    inputs = ",".join(t.value for t in sig.input_types)
    return f"({inputs})->{sig.output_type.value}"


def detect_duplicate(op: GovernedOperator) -> Optional[str]:
    """
    Check whether op is a duplicate of any already-registered GovernedOperator.

    Returns the conflicting operator_key if a duplicate is found, None if clear.

    Exact key match (same name+domain+version) → always duplicate.
    Structural match (same TypeSignature + implementation) within same name+domain
    and same version → duplicate.
    Different version with same signature → version evolution (not a duplicate error).
    """
    # 1. Exact key match
    if GovernedRegistry.has(op.operator_key):
        return op.operator_key

    # 2. Structural match within same name+domain
    sig_fp = signature_fingerprint(op)
    impl_fp = implementation_fingerprint(op)

    for existing_key in GovernedRegistry.list_operators():
        existing = GovernedRegistry.get(existing_key)
        if existing.domain != op.domain or existing.name != op.name:
            continue
        if existing.version == op.version:
            # Same version, same name/domain → duplicate regardless of content
            return existing_key
        # Different version — only flag as duplicate if signature AND impl match
        # (version evolution with same impl is allowed and expected)
        if (signature_fingerprint(existing) == sig_fp
                and implementation_fingerprint(existing) == impl_fp):
            return existing_key

    return None


def assert_no_duplicate(op: GovernedOperator) -> None:
    conflict = detect_duplicate(op)
    if conflict is not None:
        raise OperatorDuplicateError(
            f"Operator '{op.operator_key}' conflicts with existing '{conflict}'. "
            "Use a version increment for intentional evolution."
        )
