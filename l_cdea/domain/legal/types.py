from l_cdea.core.types.base import SemanticType

LEGAL_TYPES = {
    "Law":         SemanticType.CONSTRAINT,
    "Rule":        SemanticType.CONSTRAINT,
    "Clause":      SemanticType.CONSTRAINT,
    "Condition":   SemanticType.CONSTRAINT,
    "Obligation":  SemanticType.PROCESS,
    "Permission":  SemanticType.STATE,
    "Prohibition": SemanticType.CONSTRAINT,
    "Exception":   SemanticType.CONSTRAINT,
    "Case":        SemanticType.EVENT,
    "Actor":       SemanticType.ENTITY,
    "Action":      SemanticType.PROCESS,
    "Outcome":     SemanticType.STATE,
    "Violation":   SemanticType.EVENT,
    "Resolution":  SemanticType.PROCESS,
}
