from l_cdea.core.types.base import SemanticType
from l_cdea.core.compiler.resolver import _FRAME_TYPE_MAP

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)

BIOLOGY_FRAME_MAPPINGS = {
    "PHOTOSYNTHESIS_QUERY":     [((E,), E)],
    "CELL_RESPIRATION_QUERY":   [((E,), E)],
    "PROTEIN_SYNTHESIS_QUERY":  [((E,), E)],
    "CONVERT_SUBSTANCE_QUERY":  [((E, E), P)],
    "BREAK_DOWN_QUERY":         [((E,), P)],
    "BUILD_UP_QUERY":           [((E,), P)],
    "DIVIDE_CELL_QUERY":        [((E,), E)],
    "TRANSPORT_QUERY":          [((E, E, E), S)],
    "SEND_SIGNAL_QUERY":        [((E, E, EV), EV)],
    "RECEIVE_SIGNAL_QUERY":     [((E, EV), S)],
    "ACTIVATE_QUERY":           [((P,), S)],
    "INHIBIT_QUERY":            [((P,), S)],
    "MEASURE_LEVEL_QUERY":      [((E,), E)],
}


def register_biology_bindings():
    _FRAME_TYPE_MAP.update(BIOLOGY_FRAME_MAPPINGS)


def register_patterns(registry) -> None:
    from l_cdea.core.router.intent import PatternRule
    rules = [
        PatternRule(id="bio.photosynthesis", domain="biology", operator_name="PHOTOSYNTHESIS",
                    keywords=("photosynthesis",), required_slots=(), optional_slots=(), priority=110),
        PatternRule(id="bio.cell_respiration", domain="biology", operator_name="CELL_RESPIRATION",
                    keywords=("respiration",), required_slots=(), optional_slots=(), priority=105),
        PatternRule(id="bio.cell_respiration.energy", domain="biology", operator_name="CELL_RESPIRATION",
                    keywords=("cells", "energy"), required_slots=(), optional_slots=(), priority=90),
        PatternRule(id="bio.protein_synthesis", domain="biology", operator_name="PROTEIN_SYNTHESIS",
                    keywords=("protein",), required_slots=(), optional_slots=(), priority=100),
        PatternRule(id="bio.cell_division", domain="biology", operator_name="DIVIDE_CELL",
                    keywords=("cell", "divide"), required_slots=(), optional_slots=(), priority=95),
        PatternRule(id="bio.inhibit", domain="biology", operator_name="INHIBIT",
                    keywords=("inhibit",), required_slots=(), optional_slots=("substance",), priority=95),
        PatternRule(id="bio.activate", domain="biology", operator_name="ACTIVATE",
                    keywords=("activate",), required_slots=(), optional_slots=("substance",), priority=95),
        PatternRule(id="bio.measure_level", domain="biology", operator_name="MEASURE_LEVEL",
                    keywords=("level", "of"), required_slots=("substance",), optional_slots=(), priority=85),
    ]
    for rule in rules:
        registry.register(rule)
