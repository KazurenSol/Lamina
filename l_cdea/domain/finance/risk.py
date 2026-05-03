"""
Risk evaluation helpers for the finance domain.
Deterministic risk classifications — no stochastic models in V1.
"""

RISK_LEVELS = ["very_low", "low", "medium", "high", "very_high"]

ASSET_RISK_TABLE = {
    "government_bond": "very_low",
    "treasury_bill":   "very_low",
    "corporate_bond":  "low",
    "index_fund":      "low",
    "blue_chip_stock": "medium",
    "growth_stock":    "high",
    "crypto":          "very_high",
    "startup_equity":  "very_high",
}


def classify_risk(asset_name: str) -> str:
    return ASSET_RISK_TABLE.get(asset_name.lower(), "medium")


def risk_adjusted_return(expected_return: float, risk_level: str) -> float:
    """Simple risk-adjusted return: penalize higher risk."""
    penalty = {"very_low": 0.0, "low": 0.01, "medium": 0.05, "high": 0.10, "very_high": 0.20}
    return expected_return - penalty.get(risk_level, 0.05)
