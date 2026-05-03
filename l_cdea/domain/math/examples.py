"""Math domain validation examples."""
EXAMPLES = [
    {"input": "Simplify x + 0",              "expected_operator": "math.SIMPLIFY",  "expected_result": "x"},
    {"input": "Solve x^2 - 1 = 0",           "expected_operator": "math.SOLVE",     "expected_result": "x=1,-1"},
    {"input": "Evaluate f(x)=x^2 at x=3",   "expected_operator": "math.EVALUATE_FUNCTION", "expected_result": "9"},
    {"input": "Expand (x+1)^2",              "expected_operator": "math.EXPAND",    "expected_result": "x^2+2x+1"},
    {"input": "Add 3 and 5",                 "expected_operator": "math.ADD",       "expected_result": "8"},
    {"input": "Differentiate x^2 with respect to x", "expected_operator": "math.DERIVE"},
]
