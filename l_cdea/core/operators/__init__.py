"""
core/operators/ — fundamental semantic operators available system-wide.
Import this module to register all base operators into OperatorRegistry.
"""
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError
from .base import ALL_BASE_OPERATORS
from .data_ingest import LOAD_DATA


def register_all() -> None:
    """Register all core operators. Safe to call multiple times — skips already-registered."""
    for op in [*ALL_BASE_OPERATORS, LOAD_DATA]:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass  # already registered — idempotent


# Auto-register on import
register_all()

__all__ = ["register_all", "LOAD_DATA", "ALL_BASE_OPERATORS"]
