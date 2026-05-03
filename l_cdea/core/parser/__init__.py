from dataclasses import dataclass
from typing import FrozenSet, List

from .tokenizer import Token, TokenStream, tokenize
from .lexer import LexicalTag, LexicalUnit, lex
from .structure import StructureNode, StructureTree, build_structure
from .presemantic import PreSemanticFrame, generate_frames
from .exceptions import ParserError, TokenizationError, LexingError, StructureError


@dataclass
class ParsedInput:
    """Complete output contract of the parser. Passed directly to the compiler."""
    tokens: TokenStream
    lexical_units: List[LexicalUnit]
    structure: StructureTree
    presemantic_frames: FrozenSet[PreSemanticFrame]


def parse(text: str) -> ParsedInput:
    """
    Full parser pipeline: text → tokens → lexical units → structure → presemantic frames.
    Stateless and deterministic. Produces no semantic commitments.
    """
    tokens = tokenize(text)
    units = lex(tokens)
    structure = build_structure(units)
    frames = generate_frames(structure, units)
    return ParsedInput(
        tokens=tokens,
        lexical_units=units,
        structure=structure,
        presemantic_frames=frames,
    )


__all__ = [
    "parse",
    "ParsedInput",
    "Token",
    "TokenStream",
    "LexicalTag",
    "LexicalUnit",
    "StructureNode",
    "StructureTree",
    "PreSemanticFrame",
    "ParserError",
    "TokenizationError",
    "LexingError",
    "StructureError",
]
