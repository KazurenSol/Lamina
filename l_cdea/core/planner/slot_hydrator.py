"""
Slot hydrator: convert string slot values → typed TypedValue objects.

Rules:
1. Deterministic — same input always produces same output
2. Domain-aware — physics needs unit dicts, math keeps symbolic strings, etc.
3. Fails cleanly — raises PlanningError on parse failure
4. Does NOT infer unstated facts
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from l_cdea.core.types.base import SemanticType, TypedValue
from l_cdea.core.planner.plan import PlanningError

E = SemanticType.ENTITY
C = SemanticType.CONSTRAINT
A = SemanticType.ABSTRACTION

# Regex for physical quantities: "10 N", "2.5 kg", "9.8 m/s²"
_QUANTITY_RE = re.compile(r"^([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z/²³°]+.*)$")
# Regex for plain numbers
_NUMBER_RE = re.compile(r"^[-+]?\d+(?:\.\d+)?$")
# Regex for Python-style lists
_LIST_RE = re.compile(r"^\[.*\]$")


# ---------------------------------------------------------------------------
# Domain hydration hooks
# ---------------------------------------------------------------------------

def _hydrate_generic(slot: str, value: str) -> TypedValue:
    """Default: string → ENTITY."""
    if _NUMBER_RE.match(value):
        num = float(value) if "." in value else int(value)
        return TypedValue(num, E)
    if _LIST_RE.match(value):
        try:
            import ast
            return TypedValue(ast.literal_eval(value), E)
        except Exception:
            pass
    return TypedValue(value, E)


def _hydrate_physics(slot: str, value: str) -> TypedValue:
    """Physics: parse 'N m/s kg' quantity strings into {"value": float, "unit": str}."""
    m = _QUANTITY_RE.match(value.strip())
    if m:
        num_str, unit = m.group(1), m.group(2).strip()
        num = float(num_str) if "." in num_str else int(num_str)
        return TypedValue({"value": num, "unit": unit}, E)
    if _NUMBER_RE.match(value.strip()):
        return TypedValue({"value": float(value), "unit": "unknown"}, E)
    return TypedValue(value, E)


def _hydrate_math(slot: str, value: str) -> TypedValue:
    """Math: keep symbolic expressions as strings; plain numbers become numeric."""
    if _NUMBER_RE.match(value.strip()):
        num = float(value) if "." in value else int(value)
        return TypedValue(num, E)
    # Expressions stay as symbolic strings
    return TypedValue(value, E)


def _hydrate_finance(slot: str, value: str) -> TypedValue:
    """Finance: amounts become numeric, rates are constraints, others are entities."""
    if slot == "rate":
        stripped = value.replace("%", "").strip()
        try:
            return TypedValue(float(stripped) / 100 if "%" in value else float(stripped), C)
        except ValueError:
            return TypedValue(value, C)
    if slot in ("amount", "principal"):
        try:
            return TypedValue(float(value.replace(",", "")), E)
        except ValueError:
            return TypedValue(value, E)
    return TypedValue(value, E)


def _hydrate_programming(slot: str, value: str) -> TypedValue:
    """Programming: parse lists and numbers; keep expressions as strings."""
    if _LIST_RE.match(value):
        try:
            import ast
            return TypedValue(ast.literal_eval(value), E)
        except Exception:
            pass
    if _NUMBER_RE.match(value.strip()):
        num = float(value) if "." in value else int(value)
        return TypedValue(num, E)
    return TypedValue(value, E)


_DOMAIN_HYDRATORS = {
    "physics":     _hydrate_physics,
    "math":        _hydrate_math,
    "finance":     _hydrate_finance,
    "programming": _hydrate_programming,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hydrate_slots(
    domain: str,
    slots: Dict[str, str],
    required_slots: Tuple[str, ...] = (),
) -> Tuple[Dict[str, TypedValue], Optional[PlanningError]]:
    """
    Convert all slot strings to TypedValues using domain-aware hydration.
    Returns (hydrated_dict, error_or_None).
    """
    hydrator = _DOMAIN_HYDRATORS.get(domain, _hydrate_generic)
    hydrated: Dict[str, TypedValue] = {}

    for slot, raw_value in slots.items():
        try:
            hydrated[slot] = hydrator(slot, raw_value)
        except Exception as exc:
            err = PlanningError(
                code=PlanningError.SLOT_HYDRATION_FAILED,
                message=f"Failed to hydrate slot '{slot}' = {raw_value!r}: {exc}",
                details={"slot": slot, "value": raw_value, "domain": domain},
            )
            return hydrated, err

    # Check all required slots are present
    for req in required_slots:
        if req not in hydrated:
            err = PlanningError(
                code=PlanningError.SLOT_HYDRATION_FAILED,
                message=f"Required slot '{req}' missing after hydration",
                details={"slot": req, "domain": domain},
            )
            return hydrated, err

    return hydrated, None
