from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError


def _geo(name, inputs, output, fn):
    return CDLOperator(
        name=f"geography.{name}",
        signature=TypeSignature(input_types=inputs, output_type=output),
        transform=fn,
    )


LOCATED_IN = _geo("LOCATED_IN", (SemanticType.ENTITY, SemanticType.ENTITY), SemanticType.RELATION,
    lambda loc, container: TypedValue(f"{loc.value} located_in {container.value}", SemanticType.RELATION))


def _capital_of_fn(region: TypedValue) -> TypedValue:
    """
    Data-backed CAPITAL_OF.
    1. Try country_capitals_v1
    2. Try us_state_capitals_v1
    3. Symbolic fallback (no crash)
    """
    import l_cdea.data  # ensures datasets are registered
    from l_cdea.data.lookup import lookup, is_miss

    key = str(region.value)

    tv, _ = lookup("country_capitals_v1", key, operator_name="geography.CAPITAL_OF")
    if not is_miss(tv):
        return tv

    tv, _ = lookup("us_state_capitals_v1", key, operator_name="geography.CAPITAL_OF")
    if not is_miss(tv):
        return tv

    # Symbolic fallback — records a miss trace for the last dataset tried
    return TypedValue(f"capital_of({key})", SemanticType.ENTITY)


CAPITAL_OF = _geo("CAPITAL_OF", (SemanticType.ENTITY,), SemanticType.ENTITY, _capital_of_fn)

STATE_OF = _geo("STATE_OF", (SemanticType.ENTITY,), SemanticType.ENTITY,
    lambda city: TypedValue(f"state_of({city.value})", SemanticType.ENTITY))

COUNTRY_OF = _geo("COUNTRY_OF", (SemanticType.ENTITY,), SemanticType.ENTITY,
    lambda loc: TypedValue(f"country_of({loc.value})", SemanticType.ENTITY))

BORDER_WITH = _geo("BORDER_WITH", (SemanticType.ENTITY, SemanticType.ENTITY), SemanticType.RELATION,
    lambda a, b: TypedValue(f"{a.value} borders {b.value}", SemanticType.RELATION))

POPULATION_OF = _geo("POPULATION_OF", (SemanticType.ENTITY,), SemanticType.ENTITY,
    lambda region: TypedValue(f"population_of({region.value})", SemanticType.ENTITY))

GEO_LOOKUP = _geo("GEO_LOOKUP", (SemanticType.ENTITY, SemanticType.ENTITY), SemanticType.ENTITY,
    lambda key, mapping: TypedValue(
        mapping.value.get(key.value, f"unknown({key.value})") if isinstance(mapping.value, dict) else f"lookup({key.value})",
        SemanticType.ENTITY))

ALL_GEO_OPERATORS = [LOCATED_IN, CAPITAL_OF, STATE_OF, COUNTRY_OF, BORDER_WITH, POPULATION_OF, GEO_LOOKUP]


def register_geography_operators():
    for op in ALL_GEO_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
