from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Tuple

from .lexer import LexicalUnit, LexicalTag
from .structure import StructureTree


@dataclass(frozen=True)
class PreSemanticFrame:
    """
    A candidate meaning frame. Frozen and hashable for use in a set.
    No ranking, no confidence score — all frames are structurally equal at this layer.
    """
    frame_type: str
    slots: Tuple[str, ...]


def generate_frames(
    structure: StructureTree,
    units: List[LexicalUnit],
) -> FrozenSet[PreSemanticFrame]:
    """
    Generate ALL plausible candidate frames from structural evidence.
    MUST NOT prune, rank, or score. Full candidate space is produced here;
    MECP handles pruning downstream.
    """
    frames: set[PreSemanticFrame] = set()
    words = [u.form.lower() for u in units if LexicalTag.WORD in u.tags]
    word_count = len(words)

    # GENERIC frame — always present; covers any input regardless of pattern
    frames.add(PreSemanticFrame(
        frame_type="GENERIC",
        slots=tuple(f"slot_{i}" for i in range(word_count)),
    ))

    # NOMINAL — single content unit
    if word_count == 1:
        frames.add(PreSemanticFrame(frame_type="NOMINAL", slots=("entity",)))

    # PROPOSITION — two or more content words (subject + predicate minimum)
    if word_count >= 2:
        frames.add(PreSemanticFrame(frame_type="PROPOSITION", slots=("subject", "predicate")))

    # PREDICATION — copula-like structures
    if any(w in _COPULA_WORDS for w in words):
        frames.add(PreSemanticFrame(
            frame_type="PREDICATION",
            slots=("subject", "copula", "complement"),
        ))

    # ENTITY_RELATION — relational prepositions signal a relation frame
    if any(w in _RELATION_WORDS for w in words):
        frames.add(PreSemanticFrame(
            frame_type="ENTITY_RELATION",
            slots=("entity", "relation", "target"),
        ))

    # EVENT — morphological markers for verbal action
    if any(w.endswith(s) for w in words for s in _ACTION_SUFFIXES):
        frames.add(PreSemanticFrame(
            frame_type="EVENT",
            slots=("agent", "action", "patient"),
        ))

    # MULTI_CLAUSE — punctuation boundary suggests compound structure
    clause_count = sum(
        1 for child in structure.root.children if child.label == "CLAUSE"
    )
    if clause_count >= 2:
        frames.add(PreSemanticFrame(
            frame_type="MULTI_CLAUSE",
            slots=tuple(f"clause_{i}" for i in range(clause_count)),
        ))

    return frozenset(frames)


_COPULA_WORDS = frozenset({"is", "are", "was", "were", "be", "been", "being", "am"})
_RELATION_WORDS = frozenset({"of", "in", "at", "for", "from", "to", "by", "with", "on", "about", "under", "over"})
_ACTION_SUFFIXES = ("ed", "ing", "ize", "ise", "ify", "ate", "tion", "ment")
