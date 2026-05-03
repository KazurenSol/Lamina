"""
Legal rule structures for the legal domain.
All rules are deterministic. No probabilistic interpretation in V1.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class LegalRule:
    name: str
    text: str
    level: str              # constitutional, statutory, regulatory, case_law, local
    conditions: tuple = ()  # tuple of condition strings
    obligations: tuple = ()
    prohibitions: tuple = ()
    exceptions: tuple = ()


RULE_LEVELS = [
    "constitutional",
    "statutory",
    "regulatory",
    "case_law",
    "local",
]

RULE_LEVEL_RANK = {level: i for i, level in enumerate(RULE_LEVELS)}


EXAMPLE_RULES = [
    LegalRule(
        name="speed_limit",
        text="No vehicle shall exceed 65 mph on state highways.",
        level="statutory",
        prohibitions=("speed > 65",),
    ),
    LegalRule(
        name="emergency_vehicle_exception",
        text="Emergency vehicles may exceed speed limits while responding.",
        level="statutory",
        conditions=("vehicle.type == emergency",),
        exceptions=("speed_limit",),
    ),
]
