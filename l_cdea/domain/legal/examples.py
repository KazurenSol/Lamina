"""Legal domain validation examples."""
EXAMPLES = [
    {"input": "Is speeding illegal?",
     "expected_operator": "legal.CHECK_PROHIBITION"},
    {"input": "Does rule A override rule B?",
     "expected_operator": "legal.ESTABLISH_PRECEDENCE"},
    {"input": "Is this case compliant with the law?",
     "expected_operator": "legal.VALIDATE_COMPLIANCE"},
    {"input": "Resolve conflict between two clauses.",
     "expected_operator": "legal.RESOLVE_CONFLICT"},
    {"input": "Was a violation committed?",
     "expected_operator": "legal.DETECT_VIOLATION"},
    {"input": "Does this exception apply to the rule?",
     "expected_operator": "legal.APPLY_EXCEPTION"},
]
