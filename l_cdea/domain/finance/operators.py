from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)


def _fin(name, inputs, output, fn):
    return CDLOperator(name=f"finance.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


DEPOSIT = _fin("DEPOSIT", (E, E), S,
    lambda account, amount: TypedValue({"account": account.value, "balance": f"balance + {amount.value}"}, S))

WITHDRAW = _fin("WITHDRAW", (E, E), S,
    lambda account, amount: TypedValue({"account": account.value, "balance": f"balance - {amount.value}"}, S))

TRANSFER = _fin("TRANSFER", (E, E, E), S,
    lambda src, tgt, amount: TypedValue({"from": src.value, "to": tgt.value, "amount": amount.value}, S))

COMPUTE_INTEREST = _fin("COMPUTE_INTEREST", (E, C, E), E,
    lambda principal, rate, time: TypedValue(
        principal.value * rate.value * time.value
        if all(isinstance(x.value, (int, float)) for x in [principal, rate, time])
        else f"P*r*t({principal.value},{rate.value},{time.value})", E))

COMPUTE_COMPOUND_INTEREST = _fin("COMPUTE_COMPOUND_INTEREST", (E, C, E, E), E,
    lambda principal, rate, time, freq: TypedValue(
        principal.value * (1 + rate.value) ** time.value
        if all(isinstance(x.value, (int, float)) for x in [principal, rate, time])
        else f"P*(1+r)^t({principal.value},{rate.value},{time.value})", E))

UPDATE_BALANCE = _fin("UPDATE_BALANCE", (E, EV), S,
    lambda account, txn: TypedValue({"account": account.value, "after_txn": txn.value}, S))

INVEST = _fin("INVEST", (E, E), P,
    lambda asset, amount: TypedValue({"invested": amount.value, "in": asset.value}, P))

CALCULATE_RETURN = _fin("CALCULATE_RETURN", (P, E), S,
    lambda investment, time: TypedValue(f"return({investment.value},{time.value})", S))

EVALUATE_RISK = _fin("EVALUATE_RISK", (E,), C,
    lambda asset: TypedValue(f"risk({asset.value})", C))

ADD_ASSET = _fin("ADD_ASSET", (E, E), E,
    lambda portfolio, asset: TypedValue(f"portfolio+{asset.value}", E))

REMOVE_ASSET = _fin("REMOVE_ASSET", (E, E), E,
    lambda portfolio, asset: TypedValue(f"portfolio-{asset.value}", E))

COMPUTE_PORTFOLIO_VALUE = _fin("COMPUTE_PORTFOLIO_VALUE", (E,), E,
    lambda portfolio: TypedValue(f"value({portfolio.value})", E))

ADVANCE_TIME = _fin("ADVANCE_TIME", (S, E), S,
    lambda state, delta: TypedValue({"state": state.value, "time_advanced": delta.value}, S))

COMPARE_VALUES = _fin("COMPARE_VALUES", (E, E), C,
    lambda a, b: TypedValue({"a": a.value, "b": b.value, "a_gt_b": a.value > b.value
                              if isinstance(a.value, (int, float)) and isinstance(b.value, (int, float))
                              else "unknown"}, C))

ALL_FINANCE_OPERATORS = [
    DEPOSIT, WITHDRAW, TRANSFER, COMPUTE_INTEREST, COMPUTE_COMPOUND_INTEREST,
    UPDATE_BALANCE, INVEST, CALCULATE_RETURN, EVALUATE_RISK, ADD_ASSET,
    REMOVE_ASSET, COMPUTE_PORTFOLIO_VALUE, ADVANCE_TIME, COMPARE_VALUES,
]


def register_finance_operators():
    for op in ALL_FINANCE_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
