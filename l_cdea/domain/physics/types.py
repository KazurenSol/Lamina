from l_cdea.core.types.base import SemanticType

PHYSICS_TYPES = {
    "Quantity":     SemanticType.ENTITY,
    "Vector":       SemanticType.ENTITY,
    "Scalar":       SemanticType.ENTITY,
    "Force":        SemanticType.ENTITY,
    "Mass":         SemanticType.ENTITY,
    "Velocity":     SemanticType.ENTITY,
    "Acceleration": SemanticType.PROCESS,
    "Energy":       SemanticType.ENTITY,
    "System":       SemanticType.ENTITY,
    "Interaction":  SemanticType.EVENT,
    "Field":        SemanticType.ABSTRACTION,
    "PhysConstraint": SemanticType.CONSTRAINT,
    "PhysState":    SemanticType.STATE,
}
