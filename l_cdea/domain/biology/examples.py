"""Biology domain validation examples."""
EXAMPLES = [
    {"input": "What is photosynthesis?",
     "expected_operator": "biology.PHOTOSYNTHESIS"},
    {"input": "How is protein made?",
     "expected_operator": "biology.PROTEIN_SYNTHESIS"},
    {"input": "What happens when oxygen is removed?",
     "expected_operator": "biology.INHIBIT"},
    {"input": "How do cells get energy?",
     "expected_operator": "biology.CELL_RESPIRATION"},
    {"input": "How do cells divide?",
     "expected_operator": "biology.DIVIDE_CELL"},
]
