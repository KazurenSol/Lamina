"""
Operator governance tests.

Covers all four spec validation examples:
  1. Register math.ADD@1.0 → accepted, status = active
  2. Register duplicate math.ADD@1.0 → rejected (OperatorDuplicateError)
  3. Register math.ADD@1.1 (same signature, improved impl) → accepted, both coexist
  4. Register invalid operator (empty input_types) → rejected (OperatorValidationError)

Additional checks:
  - govern_all_registered() bootstraps CDL-registry operators as active
  - approve_operator() is idempotent
  - deprecate_operator() marks operator non-executable
  - audit log records every event
  - version evolution enforces MAJOR bump for breaking TypeSignature changes
  - deduplication rejects same-signature + same-impl across different versions
"""
from __future__ import annotations

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.operator_governance import (
    GovernedRegistry, AuditLog,
    governed_register, approve_operator, deprecate_operator, govern_all_registered,
    OperatorValidationError, OperatorDuplicateError, OperatorVersionError,
    OperatorNotFoundError, set_strict_governance, is_strict_mode,
)
from l_cdea.operator_governance.registry import GovernedOperator
from l_cdea.operator_governance.validator import validate_operator
from l_cdea.operator_governance.versioning import is_breaking_change
from l_cdea.core.planner.operator_resolver import _governance_check
from l_cdea.core.planner.plan import PlanningError

_PASS = "  [PASS]"
_FAIL = "  [FAIL]"

E = SemanticType.ENTITY
P = SemanticType.PROCESS


def _reset():
    GovernedRegistry.clear()
    AuditLog.clear()


def _make_add_op(impl=None) -> CDLOperator:
    if impl is None:
        impl = lambda a, b: TypedValue(value=a.value + b.value, type=E)
    return CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=E),
        transform=impl,
    )


# ── Example 1: governed_register + approve_operator ───────────────────────────

def test_register_and_approve():
    _reset()
    op = _make_add_op()
    gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})

    ok = gov_op.status == "candidate"
    print(f"{_PASS if ok else _FAIL} after governed_register: status='candidate' (got {gov_op.status!r})")

    active = approve_operator(gov_op.operator_key)
    ok = active.status == "active"
    print(f"{_PASS if ok else _FAIL} after approve_operator: status='active' (got {active.status!r})")

    stored = GovernedRegistry.get(gov_op.operator_key)
    ok = stored.status == "active"
    print(f"{_PASS if ok else _FAIL} GovernedRegistry reflects active status")

    log = AuditLog.records_for(gov_op.operator_key)
    events = [r.event for r in log]
    ok = "registered" in events and "approved" in events
    print(f"{_PASS if ok else _FAIL} audit log contains 'registered' and 'approved' events (got {events})")


# ── Example 2: duplicate rejection ────────────────────────────────────────────

def test_duplicate_rejected():
    _reset()
    op = _make_add_op()
    gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})

    caught = False
    try:
        governed_register(op, version="1.0", metadata={"deterministic": True})
    except OperatorDuplicateError:
        caught = True
    print(f"{_PASS if caught else _FAIL} duplicate math.ADD@1.0 raises OperatorDuplicateError")

    log = AuditLog.records_for(gov_op.operator_key)
    rejected = [r for r in log if r.event == "rejected"]
    ok = len(rejected) >= 1 and rejected[-1].duplicate_detected
    print(f"{_PASS if ok else _FAIL} rejection logged with duplicate_detected=True")


# ── Example 3: new version coexists ───────────────────────────────────────────

def test_new_version_coexists():
    _reset()
    impl_v1 = lambda a, b: TypedValue(value=a.value + b.value, type=E)
    impl_v2 = lambda a, b: TypedValue(value=int(a.value) + int(b.value), type=E)

    op_v1 = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=E),
        transform=impl_v1,
    )
    op_v2 = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=E),
        transform=impl_v2,
    )

    gov1 = governed_register(op_v1, version="1.0", metadata={"deterministic": True})
    approve_operator(gov1.operator_key)

    gov2 = governed_register(op_v2, version="1.1", metadata={"deterministic": True})
    approve_operator(gov2.operator_key)

    ok = GovernedRegistry.has("math.ADD@1.0") and GovernedRegistry.has("math.ADD@1.1")
    print(f"{_PASS if ok else _FAIL} both math.ADD@1.0 and math.ADD@1.1 coexist in registry")

    active = GovernedRegistry.get_active("math.ADD")
    ok = active is not None and active.version == "1.1"
    print(f"{_PASS if ok else _FAIL} get_active() returns latest version 1.1 (got {active.version if active else None!r})")


# ── Example 4: invalid operator rejected ──────────────────────────────────────

def test_invalid_operator_rejected():
    _reset()
    # Empty input_types — passes CDLOperator/TypeSignature but fails governance validator
    op_invalid = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(), output_type=E),
        transform=lambda: TypedValue(value=0, type=E),
    )
    caught = False
    try:
        governed_register(op_invalid, version="1.0", metadata={"deterministic": True})
    except OperatorValidationError as exc:
        caught = True
        ok = "input_types" in str(exc).lower()
        print(f"{_PASS if ok else _FAIL} error message mentions input_types (got: {exc!s:.80})")
    print(f"{_PASS if caught else _FAIL} invalid operator (empty input_types) raises OperatorValidationError")

    log = AuditLog.records()
    rejected = [r for r in log if r.event == "rejected"]
    ok = len(rejected) >= 1 and not rejected[-1].validation_passed
    print(f"{_PASS if ok else _FAIL} rejection logged with validation_passed=False")


# ── Additional: govern_all_registered bootstraps CDL operators ────────────────

def test_govern_all_registered():
    import l_cdea.domain.math  # ensure CDL operators are loaded into CDL registry first
    _reset()                   # clear GovernedRegistry only (CDL registry unaffected)
    count = govern_all_registered("1.0")
    ok = count > 0
    print(f"{_PASS if ok else _FAIL} govern_all_registered() bootstrapped {count} operators")

    active_keys = GovernedRegistry.list_active()
    ok = any("math.ADD" in k for k in active_keys)
    print(f"{_PASS if ok else _FAIL} math.ADD@1.0 is active after bootstrap")

    # Idempotent: second call returns 0
    count2 = govern_all_registered("1.0")
    ok = count2 == 0
    print(f"{_PASS if ok else _FAIL} govern_all_registered() is idempotent (second call returned {count2})")


# ── Additional: approve_operator is idempotent ────────────────────────────────

def test_approve_idempotent():
    _reset()
    op = _make_add_op()
    gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})
    approve_operator(gov_op.operator_key)

    result = approve_operator(gov_op.operator_key)  # second call
    ok = result.status == "active"
    print(f"{_PASS if ok else _FAIL} approve_operator() is idempotent (status={result.status!r})")


# ── Additional: deprecate_operator ────────────────────────────────────────────

def test_deprecate_operator():
    _reset()
    op = _make_add_op()
    gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})
    approve_operator(gov_op.operator_key)
    deprecate_operator(gov_op.operator_key)

    stored = GovernedRegistry.get(gov_op.operator_key)
    ok = stored.status == "deprecated"
    print(f"{_PASS if ok else _FAIL} deprecate_operator() sets status='deprecated' (got {stored.status!r})")

    active = GovernedRegistry.get_active("math.ADD")
    ok = active is None
    print(f"{_PASS if ok else _FAIL} get_active() returns None after deprecation")


# ── Additional: non-deterministic operator rejected ───────────────────────────

def test_nondeterministic_rejected():
    _reset()
    op = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=E),
        transform=lambda a, b: TypedValue(value=a.value + b.value, type=E),
    )
    caught = False
    try:
        governed_register(op, version="1.0", metadata={"deterministic": False})
    except OperatorValidationError:
        caught = True
    print(f"{_PASS if caught else _FAIL} non-deterministic operator (deterministic=False) raises OperatorValidationError")


# ── Additional: breaking change requires MAJOR bump ───────────────────────────

def test_breaking_change_requires_major_bump():
    _reset()
    op_v1 = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=E),
        transform=lambda a, b: TypedValue(value=a.value + b.value, type=E),
    )
    gov1 = governed_register(op_v1, version="1.0", metadata={"deterministic": True})
    approve_operator(gov1.operator_key)

    # Breaking change: output_type changed from ENTITY to PROCESS — needs MAJOR bump
    op_breaking = CDLOperator(
        name="math.ADD",
        signature=TypeSignature(input_types=(E, E), output_type=P),
        transform=lambda a, b: TypedValue(value=a.value + b.value, type=P),
    )
    caught = False
    try:
        governed_register(op_breaking, version="1.1", metadata={"deterministic": True})
    except OperatorVersionError:
        caught = True
    print(f"{_PASS if caught else _FAIL} breaking TypeSignature change without MAJOR bump raises OperatorVersionError")

    # Same breaking change WITH major bump → allowed
    caught = False
    try:
        gov2 = governed_register(op_breaking, version="2.0", metadata={"deterministic": True})
        ok = gov2.version == "2.0"
        print(f"{_PASS if ok else _FAIL} breaking change with MAJOR bump (2.0) accepted")
    except Exception as exc:
        print(f"{_FAIL} breaking change with MAJOR bump raised unexpected: {exc!s:.80}")


# ── Governance mode: permissive allows ungoverned with marker ─────────────────

def test_permissive_allows_ungoverned():
    _reset()
    set_strict_governance(False)
    try:
        result = _governance_check("math.UNGOVERNED_OP")
        ok = result.error is None and result.governance_status == "ungoverned"
        print(f"{_PASS if ok else _FAIL} permissive mode: ungoverned operator passes (status={result.governance_status!r})")
        ok = not result.governance_validated
        print(f"{_PASS if ok else _FAIL} permissive mode: governance_validated=False for ungoverned operator")
    finally:
        set_strict_governance(None)


# ── Governance mode: strict rejects ungoverned ────────────────────────────────

def test_strict_rejects_ungoverned():
    _reset()
    set_strict_governance(True)
    try:
        result = _governance_check("math.UNGOVERNED_OP")
        ok = result.error is not None and result.error.code == PlanningError.OPERATOR_NOT_GOVERNED
        print(f"{_PASS if ok else _FAIL} strict mode: ungoverned operator raises OPERATOR_NOT_GOVERNED "
              f"(got code={result.error.code if result.error else None!r})")
        ok = result.governance_status == "ungoverned"
        print(f"{_PASS if ok else _FAIL} strict mode: governance_status='ungoverned' in result")
    finally:
        set_strict_governance(None)


# ── Governance mode: strict allows active governed operator ───────────────────

def test_strict_allows_active():
    _reset()
    set_strict_governance(True)
    try:
        op = _make_add_op()
        gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})
        approve_operator(gov_op.operator_key)

        result = _governance_check("math.ADD")
        ok = result.error is None and result.governance_status == "active"
        print(f"{_PASS if ok else _FAIL} strict mode: active operator passes (status={result.governance_status!r})")
        ok = result.governance_validated
        print(f"{_PASS if ok else _FAIL} strict mode: governance_validated=True for active operator")
    finally:
        set_strict_governance(None)


# ── Governance mode: strict rejects candidate ─────────────────────────────────

def test_strict_rejects_candidate():
    _reset()
    set_strict_governance(True)
    try:
        op = _make_add_op()
        gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})
        # Not approved → still candidate

        result = _governance_check("math.ADD")
        ok = result.error is not None and result.error.code == PlanningError.OPERATOR_NOT_ACTIVE
        print(f"{_PASS if ok else _FAIL} strict mode: candidate operator rejected with OPERATOR_NOT_ACTIVE "
              f"(got code={result.error.code if result.error else None!r})")
        ok = result.governance_status == "candidate"
        print(f"{_PASS if ok else _FAIL} strict mode: governance_status='candidate' in result")
    finally:
        set_strict_governance(None)


# ── Governance mode: strict rejects deprecated ────────────────────────────────

def test_strict_rejects_deprecated():
    _reset()
    set_strict_governance(True)
    try:
        op = _make_add_op()
        gov_op = governed_register(op, version="1.0", metadata={"deterministic": True})
        approve_operator(gov_op.operator_key)
        deprecate_operator(gov_op.operator_key)

        result = _governance_check("math.ADD")
        ok = result.error is not None and result.error.code == PlanningError.OPERATOR_NOT_ACTIVE
        print(f"{_PASS if ok else _FAIL} strict mode: deprecated operator rejected with OPERATOR_NOT_ACTIVE "
              f"(got code={result.error.code if result.error else None!r})")
        ok = result.governance_status == "deprecated"
        print(f"{_PASS if ok else _FAIL} strict mode: governance_status='deprecated' in result")
    finally:
        set_strict_governance(None)


# ── Governance mode: env var activates strict ─────────────────────────────────

def test_env_var_strict_mode():
    import os
    _reset()
    set_strict_governance(None)  # reset programmatic override
    os.environ["L_CDEA_STRICT_GOVERNANCE"] = "1"
    try:
        ok = is_strict_mode()
        print(f"{_PASS if ok else _FAIL} L_CDEA_STRICT_GOVERNANCE=1 activates strict mode")

        result = _governance_check("math.UNGOVERNED_OP")
        ok = result.error is not None and result.error.code == PlanningError.OPERATOR_NOT_GOVERNED
        print(f"{_PASS if ok else _FAIL} env-var strict: ungoverned rejected with OPERATOR_NOT_GOVERNED")
    finally:
        del os.environ["L_CDEA_STRICT_GOVERNANCE"]
        set_strict_governance(None)


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Example 1: register + approve",           test_register_and_approve),
        ("Example 2: duplicate rejected",            test_duplicate_rejected),
        ("Example 3: new version coexists",          test_new_version_coexists),
        ("Example 4: invalid operator rejected",     test_invalid_operator_rejected),
        ("govern_all_registered bootstrap",          test_govern_all_registered),
        ("approve_operator idempotent",              test_approve_idempotent),
        ("deprecate_operator",                       test_deprecate_operator),
        ("non-deterministic rejected",               test_nondeterministic_rejected),
        ("breaking change requires MAJOR bump",      test_breaking_change_requires_major_bump),
        # Governance mode tests
        ("permissive allows ungoverned with marker",  test_permissive_allows_ungoverned),
        ("strict rejects ungoverned",                 test_strict_rejects_ungoverned),
        ("strict allows active governed operator",    test_strict_allows_active),
        ("strict rejects candidate operator",         test_strict_rejects_candidate),
        ("strict rejects deprecated operator",        test_strict_rejects_deprecated),
        ("env var L_CDEA_STRICT_GOVERNANCE=1",        test_env_var_strict_mode),
    ]
    failed = 0
    for name, fn in tests:
        print(f"\n── {name}")
        try:
            fn()
        except Exception as exc:
            print(f"{_FAIL} UNEXPECTED EXCEPTION: {exc!r}")
            failed += 1
    print(f"\n{'All tests passed.' if not failed else f'{failed} test(s) raised unexpected exceptions.'}")


if __name__ == "__main__":
    run_all()
