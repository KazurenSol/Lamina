"""Reusable legal discourse patterns."""
LEGAL_PATTERNS = [
    {"name": "rule_application",    "frame": "APPLY_RULE",          "slots": ("rule", "case")},
    {"name": "permission_check",    "frame": "CHECK_PERMISSION",    "slots": ("actor", "action")},
    {"name": "prohibition_check",   "frame": "CHECK_PROHIBITION",   "slots": ("actor", "action")},
    {"name": "violation_detection", "frame": "DETECT_VIOLATION",    "slots": ("rule", "case")},
    {"name": "conflict_resolution", "frame": "RESOLVE_CONFLICT",    "slots": ("ruleA", "ruleB")},
    {"name": "precedence_check",    "frame": "ESTABLISH_PRECEDENCE","slots": ("ruleA", "ruleB")},
    {"name": "compliance_validate", "frame": "VALIDATE_COMPLIANCE", "slots": ("case", "ruleset")},
]
