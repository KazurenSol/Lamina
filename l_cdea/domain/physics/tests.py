def test_physics_operators():
    import l_cdea.domain.physics
    from l_cdea.core.cdl.registry import OperatorRegistry
    from l_cdea.core.types.base import SemanticType, TypedValue
    from l_cdea.domain.physics.operators import (
        APPLY_FORCE, COMPUTE_ACCELERATION, COMPUTE_KINETIC_ENERGY,
        DETECT_COLLISION, CONVERT_UNITS,
    )

    assert "physics.APPLY_FORCE" in OperatorRegistry.list()
    assert "physics.COMPUTE_ACCELERATION" in OperatorRegistry.list()
    assert "physics.COMPUTE_KINETIC_ENERGY" in OperatorRegistry.list()

    E, P, S, A = (SemanticType.ENTITY, SemanticType.PROCESS,
                  SemanticType.STATE, SemanticType.ABSTRACTION)

    system = TypedValue({"name": "block"}, E)
    force  = TypedValue({"value": 10, "unit": "N"}, E)
    result = APPLY_FORCE.execute(system, force)
    assert result.type == S

    f = TypedValue({"value": 10, "unit": "N"},  E)
    m = TypedValue({"value": 2,  "unit": "kg"}, E)
    acc = COMPUTE_ACCELERATION.execute(f, m)
    assert acc.value.get("value") == 5.0

    mass = TypedValue({"value": 2, "unit": "kg"}, E)
    vel  = TypedValue({"value": 3, "unit": "m/s"}, E)
    ke = COMPUTE_KINETIC_ENERGY.execute(mass, vel)
    assert ke.value.get("value") == 9.0

    a = TypedValue("ball", E)
    b = TypedValue("wall", E)
    ev = DETECT_COLLISION.execute(a, b)
    assert "ball" in str(ev.value)

    qty  = TypedValue({"value": 1000, "unit": "m"}, E)
    unit = TypedValue("km", A)
    converted = CONVERT_UNITS.execute(qty, unit)
    assert converted.value.get("unit") == "km"

    print("Physics tests PASSED")


if __name__ == "__main__":
    test_physics_operators()
