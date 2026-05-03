"""
Temporal modeling for the finance domain.
All time inputs MUST be explicit — no hidden global clock.
"""

TIME_UNITS = ["day", "month", "quarter", "year"]


def advance_periods(balance: float, rate: float, periods: int, freq: str = "year") -> float:
    """Compound balance over N periods at given rate."""
    return balance * (1 + rate) ** periods


def simple_interest(principal: float, rate: float, time: float) -> float:
    return principal * rate * time


def compound_interest(principal: float, rate: float, time: float, frequency: int = 1) -> float:
    return principal * (1 + rate / frequency) ** (frequency * time)


TIME_RULES = [
    {"rule": "all growth/decay MUST include explicit time input"},
    {"rule": "no implicit time progression"},
    {"rule": "time tracked in DiscourseState"},
    {"rule": "MECP may prefer analytical over iterative time solutions"},
]
