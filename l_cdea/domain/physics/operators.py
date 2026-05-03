from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)


def _phys(name, inputs, output, fn):
    return CDLOperator(name=f"physics.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


def _qty(val, unit): return {"value": val, "unit": unit}


APPLY_FORCE = _phys("APPLY_FORCE", (E, E), S,
    lambda system, force: TypedValue({"system": system.value, "force": force.value}, S))

COMPUTE_ACCELERATION = _phys("COMPUTE_ACCELERATION", (E, E), P,
    lambda force, mass: TypedValue(
        _qty(force.value["value"] / mass.value["value"], "m/s²")
        if isinstance(force.value, dict) and isinstance(mass.value, dict) and mass.value.get("value", 0) != 0
        else f"F/m({force.value},{mass.value})", P))

UPDATE_VELOCITY = _phys("UPDATE_VELOCITY", (E, P, E), E,
    lambda v, a, t: TypedValue(
        _qty(v.value.get("value", 0) + a.value.get("value", 0) * t.value.get("value", 0), "m/s")
        if all(isinstance(x.value, dict) for x in [v, a, t]) else f"v+a*t({v.value},{a.value},{t.value})", E))

UPDATE_POSITION = _phys("UPDATE_POSITION", (E, E, E), S,
    lambda pos, vel, t: TypedValue(
        _qty(pos.value.get("value", 0) + vel.value.get("value", 0) * t.value.get("value", 0), "m")
        if all(isinstance(x.value, dict) for x in [pos, vel, t]) else f"x+v*t", S))

COMPUTE_KINETIC_ENERGY = _phys("COMPUTE_KINETIC_ENERGY", (E, E), E,
    lambda mass, vel: TypedValue(
        _qty(0.5 * mass.value.get("value", 0) * vel.value.get("value", 0) ** 2, "J")
        if all(isinstance(x.value, dict) for x in [mass, vel]) else f"0.5mv²", E))

COMPUTE_POTENTIAL_ENERGY = _phys("COMPUTE_POTENTIAL_ENERGY", (E, E, E), E,
    lambda mass, height, g: TypedValue(
        _qty(mass.value.get("value", 0) * g.value.get("value", 9.8) * height.value.get("value", 0), "J")
        if all(isinstance(x.value, dict) for x in [mass, height, g]) else f"mgh", E))

CONSERVE_ENERGY = _phys("CONSERVE_ENERGY", (E,), C,
    lambda system: TypedValue(f"energy_conserved({system.value})", C))

INTEGRATE_MOTION = _phys("INTEGRATE_MOTION", (S, E), S,
    lambda state, dt: TypedValue(f"integrate({state.value},{dt.value})", S))

COMPUTE_TRAJECTORY = _phys("COMPUTE_TRAJECTORY", (S, E, E), P,
    lambda init, forces, duration: TypedValue(f"trajectory({init.value},{forces.value},{duration.value})", P))

DETECT_COLLISION = _phys("DETECT_COLLISION", (E, E), EV,
    lambda a, b: TypedValue(f"collision({a.value},{b.value})", EV))

RESOLVE_COLLISION = _phys("RESOLVE_COLLISION", (E, E), S,
    lambda a, b: TypedValue(f"resolve_collision({a.value},{b.value})", S))

APPLY_FIELD_EFFECT = _phys("APPLY_FIELD_EFFECT", (A, E), S,
    lambda field, particle: TypedValue(f"field_effect({field.value},{particle.value})", S))

MEASURE = _phys("MEASURE", (E,), E,
    lambda qty: TypedValue(qty.value.get("value", qty.value) if isinstance(qty.value, dict) else qty.value, E))

COMPARE_QUANTITIES = _phys("COMPARE_QUANTITIES", (E, E), C,
    lambda a, b: TypedValue(a.value == b.value, C))

CONVERT_UNITS = _phys("CONVERT_UNITS", (E, A), E,
    lambda qty, unit: TypedValue(_qty(qty.value.get("value", qty.value), unit.value)
                                 if isinstance(qty.value, dict) else {"value": qty.value, "unit": unit.value}, E))

ALL_PHYSICS_OPERATORS = [
    APPLY_FORCE, COMPUTE_ACCELERATION, UPDATE_VELOCITY, UPDATE_POSITION,
    COMPUTE_KINETIC_ENERGY, COMPUTE_POTENTIAL_ENERGY, CONSERVE_ENERGY,
    INTEGRATE_MOTION, COMPUTE_TRAJECTORY, DETECT_COLLISION, RESOLVE_COLLISION,
    APPLY_FIELD_EFFECT, MEASURE, COMPARE_QUANTITIES, CONVERT_UNITS,
]


def register_physics_operators():
    for op in ALL_PHYSICS_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
