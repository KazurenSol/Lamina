"""Reusable geographic discourse patterns."""
GEOGRAPHY_PATTERNS = [
    {"name": "location_membership", "frame": "LOCATED_IN", "slots": ("entity", "container")},
    {"name": "capital_lookup",      "frame": "CAPITAL_OF",  "slots": ("region",)},
    {"name": "border_relation",     "frame": "BORDER_WITH", "slots": ("regionA", "regionB")},
]
