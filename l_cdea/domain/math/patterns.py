"""Reusable math discourse patterns."""
MATH_PATTERNS = [
    {"name": "arithmetic_op",    "frame": "ADD",              "slots": ("a", "b")},
    {"name": "solve_equation",   "frame": "SOLVE",            "slots": ("equation", "variable")},
    {"name": "simplify_expr",    "frame": "SIMPLIFY",         "slots": ("expression",)},
    {"name": "evaluate_fn",      "frame": "EVALUATE_FUNCTION","slots": ("function", "input")},
    {"name": "differentiate",    "frame": "DERIVE",           "slots": ("expression", "variable")},
    {"name": "integrate_expr",   "frame": "INTEGRATE",        "slots": ("expression", "variable")},
    {"name": "set_membership",   "frame": "CONTAINS",         "slots": ("set", "element")},
]
