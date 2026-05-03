"""Physics domain validation examples."""
EXAMPLES = [
    {"input": "Calculate acceleration from force and mass.",
     "expected_operator": "physics.COMPUTE_ACCELERATION"},
    {"input": "Update position after 5 seconds at constant velocity.",
     "expected_operator": "physics.UPDATE_POSITION"},
    {"input": "Compute kinetic energy.",
     "expected_operator": "physics.COMPUTE_KINETIC_ENERGY"},
    {"input": "Check if energy is conserved.",
     "expected_operator": "physics.CONSERVE_ENERGY"},
    {"input": "Detect collision between two objects.",
     "expected_operator": "physics.DETECT_COLLISION"},
]
