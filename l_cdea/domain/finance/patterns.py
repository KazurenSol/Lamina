"""Reusable finance discourse patterns."""
FINANCE_PATTERNS = [
    {"name": "account_deposit",     "frame": "DEPOSIT",                   "slots": ("account", "amount")},
    {"name": "account_withdrawal",  "frame": "WITHDRAW",                  "slots": ("account", "amount")},
    {"name": "fund_transfer",       "frame": "TRANSFER",                  "slots": ("source", "target", "amount")},
    {"name": "interest_compute",    "frame": "COMPUTE_INTEREST",          "slots": ("principal", "rate", "time")},
    {"name": "compound_growth",     "frame": "COMPUTE_COMPOUND_INTEREST", "slots": ("principal", "rate", "time", "frequency")},
    {"name": "investment_track",    "frame": "INVEST",                    "slots": ("asset", "amount")},
    {"name": "risk_assess",         "frame": "EVALUATE_RISK",             "slots": ("asset",)},
    {"name": "portfolio_value",     "frame": "COMPUTE_PORTFOLIO_VALUE",   "slots": ("portfolio",)},
]
