"""
GovernedOperatorRegistry — versioned, status-aware operator registry.

operator_key format: "{domain}.{name}@{version}"

Rules:
- No duplicate operator_key allowed.
- Same name+domain with different version: allowed (coexistence).
- Registry is deterministic (insertion-ordered, sorted output).
- Operators MUST NOT be mutated after registration.
- Only operators with status == "active" are returned by get_active().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from l_cdea.core.types.base import TypeSignature
from l_cdea.core.cdl.operator import CDLOperator


# ── Core governance types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class GovernedOperator:
    """
    A CDLOperator wrapped with governance metadata.

    operator_key = "{domain}.{name}@{version}"
    status       = "active" | "candidate" | "deprecated"
    """
    name: str
    domain: str
    version: str
    signature: TypeSignature
    implementation: Callable
    metadata: Dict = field(default_factory=dict, compare=False, hash=False)
    status: str = "candidate"

    @property
    def operator_key(self) -> str:
        return f"{self.domain}.{self.name}@{self.version}"

    @property
    def full_name(self) -> str:
        return f"{self.domain}.{self.name}"

    def to_cdl_operator(self) -> CDLOperator:
        return CDLOperator(
            name=self.full_name,
            signature=self.signature,
            transform=self.implementation,
        )

    def with_status(self, status: str) -> "GovernedOperator":
        return GovernedOperator(
            name=self.name,
            domain=self.domain,
            version=self.version,
            signature=self.signature,
            implementation=self.implementation,
            metadata=self.metadata,
            status=status,
        )


# ── Registry exceptions ────────────────────────────────────────────────────────

class GovernanceError(Exception):
    pass

class OperatorValidationError(GovernanceError):
    pass

class OperatorDuplicateError(GovernanceError):
    pass

class OperatorVersionError(GovernanceError):
    pass

class OperatorNotFoundError(GovernanceError):
    pass


# ── Registry ──────────────────────────────────────────────────────────────────

class _GovernedOperatorRegistry:
    """
    Module-level singleton. Stores GovernedOperators keyed by operator_key.
    Secondary index by full_name ("domain.name") tracks all versions.
    """

    def __init__(self) -> None:
        self._store: Dict[str, GovernedOperator] = {}          # operator_key → op
        self._by_name: Dict[str, List[str]] = {}               # full_name → [keys]

    def register(self, op: GovernedOperator) -> None:
        key = op.operator_key
        if key in self._store:
            raise OperatorDuplicateError(
                f"Operator '{key}' is already registered in the governed registry."
            )
        self._store[key] = op
        self._by_name.setdefault(op.full_name, []).append(key)

    def update_status(self, operator_key: str, status: str) -> None:
        if operator_key not in self._store:
            raise OperatorNotFoundError(f"Operator '{operator_key}' not found.")
        old = self._store[operator_key]
        self._store[operator_key] = old.with_status(status)

    def get(self, operator_key: str) -> GovernedOperator:
        if operator_key not in self._store:
            raise OperatorNotFoundError(f"Operator '{operator_key}' not found.")
        return self._store[operator_key]

    def get_active(self, full_name: str) -> Optional[GovernedOperator]:
        """
        Return the active GovernedOperator for domain.name with the highest semantic version,
        or None if no active version exists.
        """
        keys = self._by_name.get(full_name, [])
        active = [self._store[k] for k in keys if self._store[k].status == "active"]
        if not active:
            return None
        return max(active, key=lambda op: _parse_version_tuple(op.version))

    def get_active_operator(self, domain: str, name: str) -> "GovernedOperator":
        """
        Return the active GovernedOperator for (domain, name) with the highest version.
        Raises OperatorNotFoundError if no active version exists.
        """
        full_name = f"{domain}.{name}"
        op = self.get_active(full_name)
        if op is None:
            raise OperatorNotFoundError(
                f"No active governed operator found for '{full_name}'."
            )
        return op

    def get_status(self, full_name: str) -> Optional[str]:
        """
        Return the status of the active version for full_name, or None if not governed.
        Used by operator_resolver for gating.
        """
        op = self.get_active(full_name)
        if op is not None:
            return op.status
        # Check if any version (non-active) exists
        keys = self._by_name.get(full_name, [])
        if keys:
            return self._store[keys[-1]].status  # status of latest version
        return None  # not in governed registry

    def list_operators(self) -> List[str]:
        return sorted(self._store.keys())

    def list_active(self) -> List[str]:
        return sorted(k for k, op in self._store.items() if op.status == "active")

    def has(self, operator_key: str) -> bool:
        return operator_key in self._store

    def clear(self) -> None:
        self._store.clear()
        self._by_name.clear()


def _parse_version_tuple(version: str):
    """Return (major, minor) int tuple for version comparison. Falls back to (0, 0)."""
    try:
        parts = version.split(".")
        return (int(parts[0]), int(parts[1]))
    except (IndexError, ValueError):
        return (0, 0)


GovernedRegistry = _GovernedOperatorRegistry()
