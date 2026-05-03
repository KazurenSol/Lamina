"""Reusable programming discourse patterns."""
PROGRAMMING_PATTERNS = [
    {"name": "key_lookup",         "frame": "LOOKUP_KEY",          "slots": ("mapping", "key")},
    {"name": "iteration",          "frame": "ITERATE",             "slots": ("collection", "operation")},
    {"name": "conditional_branch", "frame": "CONDITIONAL_BRANCH",  "slots": ("condition", "true_path", "false_path")},
    {"name": "function_call",      "frame": "CALL_FUNCTION",       "slots": ("function", "arguments")},
    {"name": "filter_collection",  "frame": "FILTER",              "slots": ("collection", "predicate")},
    {"name": "error_handling",     "frame": "HANDLE_ERROR",        "slots": ("error", "handler")},
]
