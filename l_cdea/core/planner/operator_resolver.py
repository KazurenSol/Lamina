"""
Operator resolver: look up a CDLOperator from the registry and validate its TypeSignature
against the hydrated slot values.

Rules:
- No operator creation
- No fallback operator synthesis
- Fails with typed PlanningError if not found or arity mismatch
- Type retyping is a separate pass (retype_slots_for_operator)
- Governance gate: enforced per governance mode (permissive / strict).
  Permissive (default): ungoverned operators pass through with governance_status="ungoverned".
  Strict (L_CDEA_STRICT_GOVERNANCE=1 or set_strict_governance(True)):
    ungoverned → PlanningError(OPERATOR_NOT_GOVERNED)
    candidate/deprecated → PlanningError(OPERATOR_NOT_ACTIVE)
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

from l_cdea.core.types.base import TypedValue, SemanticType
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.planner.plan import PlanningError


class GovernanceCheckResult(NamedTuple):
    """Result of the governance gate for a single operator lookup."""
    error: Optional[PlanningError]   # non-None → resolution must stop
    governance_status: str           # "active" | "candidate" | "deprecated" | "ungoverned"
    governance_validated: bool       # True only when status == "active"


def _governance_check(op_key: str) -> GovernanceCheckResult:
    """
    Apply the governance gate.

    Permissive mode: ungoverned → pass (governance_status="ungoverned").
    Strict mode:     ungoverned → PlanningError(OPERATOR_NOT_GOVERNED).
    Both modes:      candidate/deprecated → PlanningError(OPERATOR_NOT_ACTIVE).
    """
    try:
        from l_cdea.operator_governance.registry import GovernedRegistry
        from l_cdea.operator_governance.config import is_strict_mode
    except ImportError:
        return GovernanceCheckResult(error=None, governance_status="ungoverned",
                                     governance_validated=False)

    status = GovernedRegistry.get_status(op_key)

    if status == "active":
        return GovernanceCheckResult(error=None, governance_status="active",
                                     governance_validated=True)

    if status is None:
        # Operator has no governance record
        if is_strict_mode():
            return GovernanceCheckResult(
                error=PlanningError(
                    code=PlanningError.OPERATOR_NOT_GOVERNED,
                    message=(
                        f"Operator '{op_key}' is not registered in the governed registry. "
                        "Strict governance mode requires all operators to be governed."
                    ),
                    details={"operator_key": op_key, "governance_status": "ungoverned"},
                ),
                governance_status="ungoverned",
                governance_validated=False,
            )
        # Permissive: pass through with flag
        return GovernanceCheckResult(error=None, governance_status="ungoverned",
                                     governance_validated=False)

    # status is "candidate" or "deprecated" — always rejected regardless of mode
    return GovernanceCheckResult(
        error=PlanningError(
            code=PlanningError.OPERATOR_NOT_ACTIVE,
            message=(
                f"Operator '{op_key}' is governed but not active "
                f"(status='{status}'). Only active operators are executable."
            ),
            details={"operator_key": op_key, "governance_status": status},
        ),
        governance_status=status,
        governance_validated=False,
    )


class ResolveResult(NamedTuple):
    """Result of resolve_operator(): operator, error, and governance trace."""
    operator: Optional[CDLOperator]
    error: Optional[PlanningError]
    governance_trace: Dict


def resolve_operator(
    domain: str,
    operator_name: str,
    hydrated_slots: Dict[str, TypedValue],
) -> ResolveResult:
    """
    Look up `domain.operator_name` using governance registry as primary authority.

    Resolution order:
      1. GovernedRegistry.get_active_operator(domain, operator_name) — governance authority
      2. CDL OperatorRegistry — legacy fallback (permissive mode only)

    Validates arity only — type labels are corrected by retype_slots_for_operator.
    Returns ResolveResult(operator, error, governance_trace).
    """
    op_key = f"{domain}.{operator_name}"
    gov_trace: Dict = {
        "requested_domain": domain,
        "requested_operator": operator_name,
        "resolved_operator_key": None,
        "resolved_version": None,
        "status": None,
        "governance_validated": False,
    }

    # ── Primary: governance registry ──────────────────────────────────────────
    try:
        from l_cdea.operator_governance.registry import GovernedRegistry, OperatorNotFoundError
        from l_cdea.operator_governance.config import is_strict_mode

        gov_op = GovernedRegistry.get_active_operator(domain, operator_name)
        gov_trace.update({
            "resolved_operator_key": gov_op.operator_key,
            "resolved_version": gov_op.version,
            "status": gov_op.status,
            "governance_validated": True,
        })
        op = gov_op.to_cdl_operator()
    except Exception:
        # Governance registry miss — fall back to CDL OperatorRegistry
        try:
            from l_cdea.operator_governance.config import is_strict_mode
            strict = is_strict_mode()
        except ImportError:
            strict = False

        if strict:
            gov_trace["status"] = "ungoverned"
            return ResolveResult(
                operator=None,
                error=PlanningError(
                    code=PlanningError.OPERATOR_NOT_GOVERNED,
                    message=(
                        f"Operator '{op_key}' is not registered in the governed registry. "
                        "Strict governance mode requires all operators to be governed."
                    ),
                    details={"operator_key": op_key, "governance_status": "ungoverned"},
                ),
                governance_trace=gov_trace,
            )

        # Permissive: fall back to CDL registry
        try:
            registered = OperatorRegistry.list()
        except Exception as exc:
            return ResolveResult(
                operator=None,
                error=PlanningError(
                    code=PlanningError.OPERATOR_NOT_FOUND,
                    message=f"OperatorRegistry unavailable: {exc}",
                    details={"operator_key": op_key},
                ),
                governance_trace=gov_trace,
            )

        if op_key not in registered:
            return ResolveResult(
                operator=None,
                error=PlanningError(
                    code=PlanningError.OPERATOR_NOT_FOUND,
                    message=f"Operator '{op_key}' not found in registry.",
                    details={"operator_key": op_key, "available_count": len(registered)},
                ),
                governance_trace=gov_trace,
            )

        op = OperatorRegistry.get(op_key)
        gov_trace["status"] = "ungoverned"
        gov_trace["resolved_operator_key"] = op_key

    # Also apply the status gate for governed-but-not-active (via legacy path)
    gate = _governance_check(op_key)
    if gate.error is not None:
        gov_trace["status"] = gate.governance_status
        return ResolveResult(operator=None, error=gate.error, governance_trace=gov_trace)

    sig = op.signature
    expected_arity = len(sig.input_types)
    actual_arity   = len(hydrated_slots)

    if actual_arity > expected_arity:
        return ResolveResult(
            operator=None,
            error=PlanningError(
                code=PlanningError.TYPE_MISMATCH,
                message=(
                    f"Operator '{op_key}' expects {expected_arity} input(s), "
                    f"but {actual_arity} slots were provided."
                ),
                details={
                    "operator_key": op_key,
                    "expected_arity": expected_arity,
                    "actual_arity": actual_arity,
                },
            ),
            governance_trace=gov_trace,
        )

    return ResolveResult(operator=op, error=None, governance_trace=gov_trace)


def slot_key_order(
    hydrated_slots: Dict[str, TypedValue],
    arg_order: Tuple[str, ...],
) -> List[str]:
    """
    Return deterministic slot key ordering for positional mapping to input_types.

    V1 (arg_order empty): alphabetical — matches the convention used in all
        existing operator definitions.
    V2 (arg_order non-empty): explicit order from PatternRule.arg_order, with
        any slots not listed appended alphabetically at the end.
    """
    if not arg_order:
        return sorted(hydrated_slots.keys())

    ordered = [k for k in arg_order if k in hydrated_slots]
    remaining = sorted(k for k in hydrated_slots if k not in arg_order)
    return ordered + remaining


def retype_slots_for_operator(
    op: CDLOperator,
    hydrated_slots: Dict[str, TypedValue],
    arg_order: Tuple[str, ...] = (),
) -> Dict[str, TypedValue]:
    """
    Correct each slot's SemanticType to match the operator's TypeSignature.
    Value payloads are never modified — only SemanticType labels are changed.

    Slot → input_types mapping is positional, using slot_key_order() for ordering:
      - V1 (arg_order=()): alphabetical
      - V2 (arg_order non-empty): explicit PatternRule.arg_order
    """
    sig = op.signature
    keys = slot_key_order(hydrated_slots, arg_order)
    retyped: Dict[str, TypedValue] = {}

    for i, key in enumerate(keys):
        tv = hydrated_slots[key]
        if i < len(sig.input_types):
            expected = sig.input_types[i]
            retyped[key] = TypedValue(type=expected, value=tv.value) if tv.type != expected else tv
        else:
            retyped[key] = tv

    return retyped
