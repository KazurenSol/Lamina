from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

GEOGRAPHY_FRAME_MAPPINGS = {
    "LOCATED_IN_QUERY": [
        ((SemanticType.ENTITY, SemanticType.ENTITY), SemanticType.RELATION),
    ],
    "CAPITAL_QUERY": [
        ((SemanticType.ENTITY,), SemanticType.ENTITY),
    ],
    "POPULATION_QUERY": [
        ((SemanticType.ENTITY,), SemanticType.ENTITY),
    ],
}


def register_geography_bindings():
    _FRAME_TYPE_MAP.update(GEOGRAPHY_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(
            id="geo.capital_of.region",
            domain="geography",
            operator_name="CAPITAL_OF",
            keywords=("capital", "of"),
            required_slots=("region",),
            optional_slots=(),
            priority=100,
        ),
        PatternRule(
            id="geo.located_in",
            domain="geography",
            operator_name="LOCATED_IN",
            keywords=("located", "in"),
            required_slots=("region",),
            optional_slots=(),
            priority=90,
        ),
        PatternRule(
            id="geo.population_of",
            domain="geography",
            operator_name="POPULATION_OF",
            keywords=("population", "of"),
            required_slots=("region",),
            optional_slots=(),
            priority=90,
        ),
        PatternRule(
            id="geo.border_with",
            domain="geography",
            operator_name="BORDER_WITH",
            keywords=("border", "countries"),
            required_slots=("region",),
            optional_slots=(),
            priority=85,
        ),
        PatternRule(
            id="geo.country_of",
            domain="geography",
            operator_name="COUNTRY_OF",
            keywords=("country", "of"),
            required_slots=("region",),
            optional_slots=(),
            priority=85,
        ),
    ]
    for rule in rules:
        registry.register(rule)
