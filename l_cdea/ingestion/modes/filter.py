"""
Dictionary-mode chunk filter.

Rejects:
  - single-word chunks (no whitespace after stripping)
  - punctuation-only or whitespace-only strings
  - fragments with no recognizable verb (incomplete statements)

A "verb" is any token from the known verb set. This is a closed-form
heuristic — no NLP library required.
"""
from __future__ import annotations

import re

_VERBS = frozenset({
    "is", "are", "was", "were", "be", "been", "being",
    "means", "mean", "meant",
    "refers", "refer", "referred",
    "denotes", "denote", "denoted",
    "designates", "designate",
    "defines", "define", "defined",
    "describes", "describe", "described",
    "represents", "represent",
    "involves", "involve",
    "includes", "include",
    "contains", "contain",
    "equals", "equal",
    "has", "have", "had",
    "depends", "depend", "depended",
    "requires", "require", "required",
    "causes", "cause", "caused",
    "affects", "affect",
    "produces", "produce", "produced",
})

_PUNCTUATION_ONLY = re.compile(r"^[\W_]+$")


def is_valid_dictionary_chunk(text: str) -> bool:
    """
    Return True if text is acceptable as a dictionary-mode chunk.
    Rejects single-word, punctuation-only, and verb-free fragments.
    """
    stripped = text.strip()
    if not stripped:
        return False

    # Punctuation-only
    if _PUNCTUATION_ONLY.match(stripped):
        return False

    tokens = stripped.split()

    # Single-word
    if len(tokens) < 2:
        return False

    # Must contain at least one recognized verb
    lower_tokens = {t.lower().rstrip(".,;:!?") for t in tokens}
    if not lower_tokens & _VERBS:
        return False

    return True
