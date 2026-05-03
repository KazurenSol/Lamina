"""
operator_governance — public API for operator lifecycle management.

Entry points:
  governed_register(cdl_op, version, metadata) → GovernedOperator (candidate)
  approve_operator(operator_key)               → GovernedOperator (active)
  deprecate_operator(operator_key)             → None
  govern_all_registered(version)               → int (newly governed count)

Query:
  GovernedRegistry.get(operator_key)           → GovernedOperator
  GovernedRegistry.get_active(full_name)       → Optional[GovernedOperator]
  GovernedRegistry.get_status(full_name)       → Optional[str]

Exceptions:
  GovernanceError
  OperatorValidationError
  OperatorDuplicateError
  OperatorVersionError
  OperatorNotFoundError

Audit:
  AuditLog.records()                           → List[OperatorAuditRecord]
  AuditLog.records_for(operator_key)           → List[OperatorAuditRecord]
"""
from l_cdea.operator_governance.registry import (
    GovernedOperator,
    GovernedRegistry,
    GovernanceError,
    OperatorValidationError,
    OperatorDuplicateError,
    OperatorVersionError,
    OperatorNotFoundError,
)
from l_cdea.operator_governance.audit import (
    AuditLog,
    OperatorAuditRecord,
)
from l_cdea.operator_governance.validator import validate_operator, assert_valid
from l_cdea.operator_governance.approval import (
    governed_register,
    approve_operator,
    deprecate_operator,
    govern_all_registered,
)
from l_cdea.operator_governance.config import (
    is_strict_mode,
    set_strict_governance,
)

__all__ = [
    # Types
    "GovernedOperator",
    "OperatorAuditRecord",
    # Registry
    "GovernedRegistry",
    # Exceptions
    "GovernanceError",
    "OperatorValidationError",
    "OperatorDuplicateError",
    "OperatorVersionError",
    "OperatorNotFoundError",
    # Audit
    "AuditLog",
    # Validators
    "validate_operator",
    "assert_valid",
    # Lifecycle
    "governed_register",
    "approve_operator",
    "deprecate_operator",
    "govern_all_registered",
    # Mode
    "is_strict_mode",
    "set_strict_governance",
]
