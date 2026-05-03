from l_cdea.core.types.base import SemanticType

FINANCE_TYPES = {
    "Money":      SemanticType.ENTITY,
    "Account":    SemanticType.ENTITY,
    "Transaction": SemanticType.EVENT,
    "Balance":    SemanticType.STATE,
    "Rate":       SemanticType.CONSTRAINT,
    "Time":       SemanticType.ENTITY,
    "Investment": SemanticType.PROCESS,
    "Return":     SemanticType.STATE,
    "Risk":       SemanticType.CONSTRAINT,
    "Asset":      SemanticType.ENTITY,
    "Liability":  SemanticType.ENTITY,
    "Portfolio":  SemanticType.ENTITY,
    "CashFlow":   SemanticType.EVENT,
}
