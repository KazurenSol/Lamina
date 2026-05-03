from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)

FINANCE_FRAME_MAPPINGS = {
    "DEPOSIT_QUERY":                   [((E, E), S)],
    "WITHDRAW_QUERY":                  [((E, E), S)],
    "TRANSFER_QUERY":                  [((E, E, E), S)],
    "COMPUTE_INTEREST_QUERY":          [((E, C, E), E)],
    "COMPUTE_COMPOUND_INTEREST_QUERY": [((E, C, E, E), E)],
    "UPDATE_BALANCE_QUERY":            [((E, EV), S)],
    "INVEST_QUERY":                    [((E, E), P)],
    "CALCULATE_RETURN_QUERY":          [((P, E), S)],
    "EVALUATE_RISK_QUERY":             [((E,), C)],
    "ADD_ASSET_QUERY":                 [((E, E), E)],
    "REMOVE_ASSET_QUERY":              [((E, E), E)],
    "COMPUTE_PORTFOLIO_VALUE_QUERY":   [((E,), E)],
    "ADVANCE_TIME_QUERY":              [((S, E), S)],
    "COMPARE_VALUES_QUERY":            [((E, E), C)],
}


def register_finance_bindings():
    _FRAME_TYPE_MAP.update(FINANCE_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="fin.deposit", domain="finance", operator_name="DEPOSIT",
                    keywords=("deposit",), required_slots=("account",), optional_slots=("amount",), priority=100),
        PatternRule(id="fin.withdraw", domain="finance", operator_name="WITHDRAW",
                    keywords=("withdraw",), required_slots=("account",), optional_slots=("amount",), priority=100),
        PatternRule(id="fin.transfer", domain="finance", operator_name="TRANSFER",
                    keywords=("transfer",), required_slots=(), optional_slots=("amount", "account"), priority=100),
        PatternRule(id="fin.compound_interest", domain="finance", operator_name="COMPUTE_COMPOUND_INTEREST",
                    keywords=("compound", "interest"), required_slots=(), optional_slots=("principal", "rate"), priority=110),
        PatternRule(id="fin.interest", domain="finance", operator_name="COMPUTE_INTEREST",
                    keywords=("interest",), required_slots=(), optional_slots=("principal", "rate"), priority=95),
        PatternRule(id="fin.portfolio_value", domain="finance", operator_name="COMPUTE_PORTFOLIO_VALUE",
                    keywords=("portfolio", "value"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="fin.evaluate_risk", domain="finance", operator_name="EVALUATE_RISK",
                    keywords=("risk",), required_slots=(), optional_slots=(), priority=90),
        PatternRule(id="fin.calculate_return", domain="finance", operator_name="CALCULATE_RETURN",
                    keywords=("return", "investment"), required_slots=(), optional_slots=(), priority=95),
    ]
    for rule in rules:
        registry.register(rule)
