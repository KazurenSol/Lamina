from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)

PHYSICS_FRAME_MAPPINGS = {
    "APPLY_FORCE_QUERY":             [((E, E), S)],
    "COMPUTE_ACCELERATION_QUERY":    [((E, E), P)],
    "UPDATE_VELOCITY_QUERY":         [((E, P, E), E)],
    "UPDATE_POSITION_QUERY":         [((E, E, E), S)],
    "COMPUTE_KINETIC_ENERGY_QUERY":  [((E, E), E)],
    "COMPUTE_POTENTIAL_ENERGY_QUERY":[((E, E, E), E)],
    "CONSERVE_ENERGY_QUERY":         [((E,), C)],
    "INTEGRATE_MOTION_QUERY":        [((S, E), S)],
    "COMPUTE_TRAJECTORY_QUERY":      [((S, E, E), P)],
    "DETECT_COLLISION_QUERY":        [((E, E), EV)],
    "RESOLVE_COLLISION_QUERY":       [((E, E), S)],
    "APPLY_FIELD_EFFECT_QUERY":      [((A, E), S)],
    "MEASURE_QUERY":                 [((E,), E)],
    "COMPARE_QUANTITIES_QUERY":      [((E, E), C)],
    "CONVERT_UNITS_QUERY":           [((E, A), E)],
}


def register_physics_bindings():
    _FRAME_TYPE_MAP.update(PHYSICS_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="physics.compute_acceleration", domain="physics", operator_name="COMPUTE_ACCELERATION",
                    keywords=("acceleration", "force", "mass"),
                    required_slots=("force", "mass"), optional_slots=(), priority=110),
        PatternRule(id="physics.compute_acceleration.calculate", domain="physics", operator_name="COMPUTE_ACCELERATION",
                    keywords=("calculate", "acceleration"),
                    required_slots=(), optional_slots=("force", "mass"), priority=95),
        PatternRule(id="physics.kinetic_energy", domain="physics", operator_name="COMPUTE_KINETIC_ENERGY",
                    keywords=("kinetic", "energy"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="physics.potential_energy", domain="physics", operator_name="COMPUTE_POTENTIAL_ENERGY",
                    keywords=("potential", "energy"), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="physics.update_velocity", domain="physics", operator_name="UPDATE_VELOCITY",
                    keywords=("velocity",), required_slots=(), optional_slots=("time",), priority=85),
        PatternRule(id="physics.update_position", domain="physics", operator_name="UPDATE_POSITION",
                    keywords=("position",), required_slots=(), optional_slots=("time",), priority=85),
        PatternRule(id="physics.detect_collision", domain="physics", operator_name="DETECT_COLLISION",
                    keywords=("collision",), required_slots=(), optional_slots=(), priority=90),
        PatternRule(id="physics.conserve_energy", domain="physics", operator_name="CONSERVE_ENERGY",
                    keywords=("energy", "conserved"), required_slots=(), optional_slots=(), priority=95),
    ]
    for rule in rules:
        registry.register(rule)
