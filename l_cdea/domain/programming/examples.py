"""Programming domain validation examples."""
EXAMPLES = [
    {"input": "Create a function that returns the square of a number.",
     "expected_operator": "programming.DEFINE_FUNCTION"},
    {"input": "Get the capital of Texas from the state capital dictionary.",
     "expected_operator": "programming.LOOKUP_KEY"},
    {"input": "Return all numbers greater than 10.",
     "expected_operator": "programming.FILTER"},
    {"input": "Find the first item matching the condition.",
     "expected_operator": "programming.ITERATE"},
    {"input": "Assign x = x + 1.",
     "expected_operator": "programming.ASSIGN"},
    {"input": "If x > 0 return A else return B.",
     "expected_operator": "programming.CONDITIONAL_BRANCH"},
]
