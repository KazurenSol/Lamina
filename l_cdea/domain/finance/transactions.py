"""
Transaction types and ledger helpers for the finance domain.
"""
from l_cdea.core.types.base import SemanticType, TypedValue

EV = SemanticType.EVENT
S = SemanticType.STATE

TRANSACTION_TYPES = [
    "deposit",
    "withdrawal",
    "transfer",
    "interest_credit",
    "fee_debit",
    "dividend",
    "investment",
]


def make_transaction(txn_type: str, amount: float, account: str) -> TypedValue:
    return TypedValue({"type": txn_type, "amount": amount, "account": account}, EV)


def apply_transaction(balance: float, txn: dict) -> float:
    """Apply a transaction dict to a numeric balance."""
    if not isinstance(txn, dict):
        return balance
    txn_type = txn.get("type", "")
    amount = txn.get("amount", 0)
    if txn_type in ("deposit", "interest_credit", "dividend"):
        return balance + amount
    if txn_type in ("withdrawal", "fee_debit"):
        return balance - amount
    return balance
