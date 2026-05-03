from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.registry import OperatorRegistry
from l_cdea.core.cdl.exceptions import InvalidOperatorError

E, P, S, C, A, EV = (SemanticType.ENTITY, SemanticType.PROCESS, SemanticType.STATE,
                      SemanticType.CONSTRAINT, SemanticType.ABSTRACTION, SemanticType.EVENT)


def _bio(name, inputs, output, fn):
    return CDLOperator(name=f"biology.{name}",
                       signature=TypeSignature(input_types=inputs, output_type=output),
                       transform=fn)


PHOTOSYNTHESIS = _bio("PHOTOSYNTHESIS", (E,), E,
    lambda inputs: TypedValue({"process": "photosynthesis", "inputs": inputs.value,
                                "outputs": {"glucose": 1, "oxygen": 6}}, E))

CELL_RESPIRATION = _bio("CELL_RESPIRATION", (E,), E,
    lambda inputs: TypedValue({"process": "cell_respiration", "inputs": inputs.value,
                                "outputs": {"ATP": "energy", "CO2": 6, "H2O": 6}}, E))

PROTEIN_SYNTHESIS = _bio("PROTEIN_SYNTHESIS", (E,), E,
    lambda dna: TypedValue({"process": "protein_synthesis", "from": dna.value,
                             "steps": ["DNA→RNA", "RNA→Protein"]}, E))

CONVERT_SUBSTANCE = _bio("CONVERT_SUBSTANCE", (E, E), P,
    lambda inp, out: TypedValue(f"convert({inp.value} → {out.value})", P))

BREAK_DOWN = _bio("BREAK_DOWN", (E,), P,
    lambda substance: TypedValue(f"break_down({substance.value})", P))

BUILD_UP = _bio("BUILD_UP", (E,), P,
    lambda substance: TypedValue(f"build_up({substance.value})", P))

DIVIDE_CELL = _bio("DIVIDE_CELL", (E,), E,
    lambda cell: TypedValue({"process": "cell_division", "parent": cell.value}, E))

TRANSPORT = _bio("TRANSPORT", (E, E, E), S,
    lambda substance, src, dst: TypedValue(f"transport({substance.value}: {src.value}→{dst.value})", S))

SEND_SIGNAL = _bio("SEND_SIGNAL", (E, E, EV), EV,
    lambda src, tgt, sig: TypedValue(f"signal({sig.value}: {src.value}→{tgt.value})", EV))

RECEIVE_SIGNAL = _bio("RECEIVE_SIGNAL", (E, EV), S,
    lambda target, signal: TypedValue(f"received({signal.value} at {target.value})", S))

ACTIVATE = _bio("ACTIVATE", (P,), S,
    lambda process: TypedValue({"activated": process.value}, S))

INHIBIT = _bio("INHIBIT", (P,), S,
    lambda process: TypedValue({"inhibited": process.value}, S))

MEASURE_LEVEL = _bio("MEASURE_LEVEL", (E,), E,
    lambda substance: TypedValue(f"level({substance.value})", E))

ALL_BIOLOGY_OPERATORS = [
    PHOTOSYNTHESIS, CELL_RESPIRATION, PROTEIN_SYNTHESIS, CONVERT_SUBSTANCE,
    BREAK_DOWN, BUILD_UP, DIVIDE_CELL, TRANSPORT, SEND_SIGNAL, RECEIVE_SIGNAL,
    ACTIVATE, INHIBIT, MEASURE_LEVEL,
]


def register_biology_operators():
    for op in ALL_BIOLOGY_OPERATORS:
        try:
            OperatorRegistry.register(op)
        except InvalidOperatorError:
            pass


def register_governed_operators():
    """Bootstrap all domain operators through the governance layer. Idempotent."""
    from l_cdea.operator_governance.approval import govern_all_registered
    govern_all_registered()
