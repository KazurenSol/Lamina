from l_cdea.core.types.base import SemanticType

PROGRAMMING_TYPES = {
    "Program":     SemanticType.PROCESS,
    "Function":    SemanticType.PROCESS,
    "Variable":    SemanticType.ENTITY,
    "Value":       SemanticType.ENTITY,
    "Collection":  SemanticType.ENTITY,
    "Mapping":     SemanticType.ENTITY,
    "Expression":  SemanticType.PROCESS,
    "Statement":   SemanticType.EVENT,
    "Condition":   SemanticType.CONSTRAINT,
    "Loop":        SemanticType.PROCESS,
    "Branch":      SemanticType.PROCESS,
    "ReturnValue": SemanticType.STATE,
    "Error":       SemanticType.STATE,
}
