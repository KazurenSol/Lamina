"""
Governance mode configuration.

Modes:
  permissive — ungoverned operators pass through with a warning/trace flag (default)
  strict     — ungoverned operators are rejected with PlanningError(OPERATOR_NOT_GOVERNED)

Activation:
  1. Environment variable:  L_CDEA_STRICT_GOVERNANCE=1
  2. Programmatic:          set_strict_governance(True)

The programmatic flag always overrides the environment variable when set.
Reset with set_strict_governance(None) to fall back to env-var detection.
"""
from __future__ import annotations

import os
from typing import Optional


_STRICT_OVERRIDE: Optional[bool] = None  # None = use env var


def is_strict_mode() -> bool:
    """Return True if strict governance is active."""
    if _STRICT_OVERRIDE is not None:
        return _STRICT_OVERRIDE
    return os.environ.get("L_CDEA_STRICT_GOVERNANCE", "").strip() == "1"


def set_strict_governance(strict: Optional[bool]) -> None:
    """
    Set governance mode programmatically.

    strict=True   → strict mode (ungoverned operators rejected)
    strict=False  → permissive mode (ungoverned pass through)
    strict=None   → reset to env-var detection
    """
    global _STRICT_OVERRIDE
    _STRICT_OVERRIDE = strict
