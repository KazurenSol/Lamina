"""
Operator audit log — append-only record of every registration, rejection, and approval.

Rules:
- Every registration attempt MUST be logged (success or failure).
- Every rejection MUST be logged with reason.
- Every approval MUST be logged.
- Log is append-only: records are never removed or modified.
- Log is deterministic: timestamp_index is a monotonic counter, not wall-clock time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class OperatorAuditRecord:
    """Immutable record of a single governance event."""
    operator_key: str
    version: str
    event: str              # "register_attempt" | "registered" | "rejected" | "approved" | "deprecated"
    validation_passed: bool
    duplicate_detected: bool
    approved: bool
    timestamp_index: int
    notes: Dict = field(default_factory=dict, compare=False, hash=False)


class _OperatorAuditLog:
    """
    Module-level singleton. Append-only. Thread-unsafe in V1 (single-process).
    timestamp_index is a monotonic counter — not wall-clock time.
    """

    def __init__(self) -> None:
        self._records: List[OperatorAuditRecord] = []
        self._counter: int = 0

    def record(
        self,
        operator_key: str,
        version: str,
        event: str,
        validation_passed: bool = False,
        duplicate_detected: bool = False,
        approved: bool = False,
        notes: Dict | None = None,
    ) -> OperatorAuditRecord:
        rec = OperatorAuditRecord(
            operator_key=operator_key,
            version=version,
            event=event,
            validation_passed=validation_passed,
            duplicate_detected=duplicate_detected,
            approved=approved,
            timestamp_index=self._counter,
            notes=notes or {},
        )
        self._records.append(rec)
        self._counter += 1
        return rec

    def records(self) -> List[OperatorAuditRecord]:
        return list(self._records)

    def records_for(self, operator_key: str) -> List[OperatorAuditRecord]:
        return [r for r in self._records if r.operator_key == operator_key]

    def clear(self) -> None:
        self._records.clear()
        self._counter = 0


AuditLog = _OperatorAuditLog()
