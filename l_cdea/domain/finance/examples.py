"""Finance domain validation examples."""
EXAMPLES = [
    {"input": "Deposit 100 into account.",
     "expected_operator": "finance.DEPOSIT"},
    {"input": "Compute compound interest.",
     "expected_operator": "finance.COMPUTE_COMPOUND_INTEREST"},
    {"input": "What is the return on this investment?",
     "expected_operator": "finance.CALCULATE_RETURN"},
    {"input": "Compare two investments.",
     "expected_operator": "finance.COMPARE_VALUES"},
    {"input": "Evaluate the risk of this asset.",
     "expected_operator": "finance.EVALUATE_RISK"},
    {"input": "Compute portfolio value.",
     "expected_operator": "finance.COMPUTE_PORTFOLIO_VALUE"},
]
