from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .exceptions import StructureError
from .lexer import LexicalUnit, LexicalTag


@dataclass
class StructureNode:
    """A node in the syntactic skeleton. Carries grouping label and span, not meaning."""
    label: str
    span: Tuple[int, int]
    children: List[StructureNode] = field(default_factory=list)
    units: List[LexicalUnit] = field(default_factory=list)


@dataclass
class StructureTree:
    """Syntactic skeleton of parsed input. No semantic roles assigned."""
    root: StructureNode


def build_structure(units: List[LexicalUnit]) -> StructureTree:
    """
    Group lexical units into a syntactic skeleton.
    PUNCT tokens act as clause boundaries. Consecutive WORDs/NUMBERs form PHRASEs.
    No semantic role assignment.
    """
    if not units:
        raise StructureError("Cannot build structure from empty unit list")

    phrases: List[StructureNode] = []
    current: List[LexicalUnit] = []

    for unit in units:
        if LexicalTag.PUNCT in unit.tags:
            if current:
                phrases.append(_make_phrase(current))
                current = []
            phrases.append(StructureNode(label="PUNCT", span=unit.span, units=[unit]))
        else:
            current.append(unit)

    if current:
        phrases.append(_make_phrase(current))

    if len(phrases) == 1:
        root = phrases[0]
    else:
        span = (phrases[0].span[0], phrases[-1].span[1])
        root = StructureNode(label="CLAUSE", span=span, children=phrases)

    return StructureTree(root=root)


def _make_phrase(units: List[LexicalUnit]) -> StructureNode:
    span = (units[0].span[0], units[-1].span[1])
    if len(units) == 1:
        return StructureNode(label="WORD", span=span, units=units)
    word_nodes = [
        StructureNode(label="WORD", span=u.span, units=[u]) for u in units
    ]
    return StructureNode(label="PHRASE", span=span, children=word_nodes, units=units)
