from l_cdea.core.types.base import SemanticType

BIOLOGY_TYPES = {
    "Cell":        SemanticType.ENTITY,
    "Organism":    SemanticType.ENTITY,
    "Tissue":      SemanticType.ENTITY,
    "Organ":       SemanticType.ENTITY,
    "Molecule":    SemanticType.ENTITY,
    "Protein":     SemanticType.ENTITY,
    "DNA":         SemanticType.ENTITY,
    "RNA":         SemanticType.ENTITY,
    "BioProcess":  SemanticType.PROCESS,
    "Reaction":    SemanticType.EVENT,
    "Energy":      SemanticType.ENTITY,
    "Nutrient":    SemanticType.ENTITY,
    "Signal":      SemanticType.EVENT,
    "BioState":    SemanticType.STATE,
    "BioConstraint": SemanticType.CONSTRAINT,
}
