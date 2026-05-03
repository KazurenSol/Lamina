"""Reusable physics discourse patterns."""
PHYSICS_PATTERNS = [
    {"name": "force_application",   "frame": "APPLY_FORCE",           "slots": ("system", "force")},
    {"name": "velocity_update",     "frame": "UPDATE_VELOCITY",       "slots": ("velocity", "acceleration", "time")},
    {"name": "position_update",     "frame": "UPDATE_POSITION",       "slots": ("position", "velocity", "time")},
    {"name": "kinetic_energy",      "frame": "COMPUTE_KINETIC_ENERGY","slots": ("mass", "velocity")},
    {"name": "energy_conservation", "frame": "CONSERVE_ENERGY",       "slots": ("system",)},
    {"name": "collision_detect",    "frame": "DETECT_COLLISION",      "slots": ("bodyA", "bodyB")},
    {"name": "unit_conversion",     "frame": "CONVERT_UNITS",         "slots": ("quantity", "target_unit")},
]
