"""
SI unit system for the physics domain.
All quantities MUST carry units. Dimensionally invalid operations raise errors.
"""

SI_UNITS = {
    "length":       "m",
    "mass":         "kg",
    "time":         "s",
    "velocity":     "m/s",
    "acceleration": "m/s²",
    "force":        "N",
    "energy":       "J",
    "power":        "W",
    "pressure":     "Pa",
    "temperature":  "K",
}

UNIT_CONVERSIONS = {
    ("km", "m"):    1000.0,
    ("cm", "m"):    0.01,
    ("mm", "m"):    0.001,
    ("g",  "kg"):   0.001,
    ("km/h", "m/s"): 1 / 3.6,
    ("kJ", "J"):    1000.0,
    ("MJ", "J"):    1_000_000.0,
}

COMPATIBLE_OPERATIONS = {
    "ADD":      "same unit required",
    "SUBTRACT": "same unit required",
    "MULTIPLY": "units multiply",
    "DIVIDE":   "units divide",
}


def convert(value: float, from_unit: str, to_unit: str) -> float:
    key = (from_unit, to_unit)
    if key in UNIT_CONVERSIONS:
        return value * UNIT_CONVERSIONS[key]
    inv_key = (to_unit, from_unit)
    if inv_key in UNIT_CONVERSIONS:
        return value / UNIT_CONVERSIONS[inv_key]
    raise ValueError(f"No conversion from {from_unit} to {to_unit}")


def make_quantity(value: float, unit: str) -> dict:
    return {"value": value, "unit": unit}
