from l_cdea.core.types.base import SemanticType

# Geography domain type → core SemanticType mapping
GEOGRAPHY_TYPES = {
    "Location":   SemanticType.ENTITY,
    "Country":    SemanticType.ENTITY,
    "State":      SemanticType.ENTITY,
    "City":       SemanticType.ENTITY,
    "Region":     SemanticType.ENTITY,
    "Capital":    SemanticType.ENTITY,
    "Border":     SemanticType.RELATION,
    "Population": SemanticType.ENTITY,
    "Territory":  SemanticType.ENTITY,
}
