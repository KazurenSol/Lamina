"""Geography domain validation examples."""
EXAMPLES = [
    {"input": "What is the capital of Texas?",     "expected_operator": "geography.CAPITAL_OF"},
    {"input": "Is France located in Europe?",      "expected_operator": "geography.LOCATED_IN"},
    {"input": "What countries border Germany?",    "expected_operator": "geography.BORDER_WITH"},
    {"input": "What is the population of Japan?",  "expected_operator": "geography.POPULATION_OF"},
]
