from l_cdea.core.types.base import SemanticType

MATH_TYPES = {
    "Number":     SemanticType.ENTITY,
    "Variable":   SemanticType.ENTITY,
    "Expression": SemanticType.PROCESS,
    "Equation":   SemanticType.CONSTRAINT,
    "Function":   SemanticType.PROCESS,
    "Set":        SemanticType.ENTITY,
    "Vector":     SemanticType.ENTITY,
    "Matrix":     SemanticType.ENTITY,
    "Operator":   SemanticType.ABSTRACTION,
    "Inequality": SemanticType.CONSTRAINT,
}
