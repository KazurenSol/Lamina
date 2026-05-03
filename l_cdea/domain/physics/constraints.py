"""
Physical conservation laws and constraint validators for the physics domain.
"""
from l_cdea.core.types.base import SemanticType, TypedValue

C = SemanticType.CONSTRAINT


def energy_conserved(before: dict, after: dict) -> TypedValue:
    """Check KE + PE is conserved (within floating-point tolerance)."""
    if not (isinstance(before, dict) and isinstance(after, dict)):
        return TypedValue(f"energy_conserved({before}, {after})", C)
    total_before = before.get("KE", 0) + before.get("PE", 0)
    total_after = after.get("KE", 0) + after.get("PE", 0)
    return TypedValue(abs(total_before - total_after) < 1e-9, C)


def momentum_conserved(p_before: float, p_after: float) -> TypedValue:
    return TypedValue(abs(p_before - p_after) < 1e-9, C)


PHYSICS_CONSTRAINTS = [
    {"name": "energy_conservation",   "law": "KE + PE = constant",   "validator": "energy_conserved"},
    {"name": "momentum_conservation", "law": "Σp = constant",         "validator": "momentum_conserved"},
    {"name": "newton_second",         "law": "F = m * a",             "validator": "compute_acceleration"},
    {"name": "unit_compatibility",    "law": "operations require matching units"},
]
