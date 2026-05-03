from dataclasses import dataclass
from typing import List

from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.parser import ParsedInput
from .resolver import TypedInterpretation, TypedInterpretationSet, resolve
from .binding import OperatorBinding, OperatorBindingSet, bind
from .builder import build_graphs
from .strategy import InterpretationStrategy, InterpretationStrategySet, stratify
from .exceptions import CompilerError, TypeResolutionError, BindingError, GraphConstructionError


@dataclass
class CompiledOutput:
    """Output contract of the compiler. Passed to CAS → MECP → Executor."""
    graphs: List[CDLGraph]
    bindings: OperatorBindingSet
    interpretations: TypedInterpretationSet
    strategies: InterpretationStrategySet


def compile(parsed_input: ParsedInput) -> CompiledOutput:
    """
    Convert ParsedInput → CompiledOutput.
    Pipeline: frame resolution → operator binding → graph construction → strategy grouping.
    Stateless. No execution, no pruning, no DiscourseState access.
    """
    interpretations = resolve(parsed_input.presemantic_frames)
    bindings = bind(interpretations)
    graphs = build_graphs(bindings, parsed_input.lexical_units)
    strategies = stratify(bindings)
    return CompiledOutput(
        graphs=graphs,
        bindings=bindings,
        interpretations=interpretations,
        strategies=strategies,
    )


__all__ = [
    "compile",
    "CompiledOutput",
    "TypedInterpretation",
    "TypedInterpretationSet",
    "OperatorBinding",
    "OperatorBindingSet",
    "InterpretationStrategy",
    "InterpretationStrategySet",
    "CompilerError",
    "TypeResolutionError",
    "BindingError",
    "GraphConstructionError",
]
