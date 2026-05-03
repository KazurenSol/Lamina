"""
Query normalization for paraphrase matching.

normalize_query(text) → str:
  1. lowercase
  2. strip punctuation
  3. collapse whitespace
  4. remove leading polite phrases
  5. preserve key verbs

Designed to be called BEFORE parse() when downstream callers want clean input.
The router patterns are also written to work WITHOUT pre-normalization — polite-phrase
words are in the slot_filler term skip set so they never contaminate term extraction.
"""
from __future__ import annotations

import re
import string
from typing import List, Tuple

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)

# Leading polite phrases to strip, longest-match first
_POLITE_PREFIXES: Tuple[Tuple[str, ...], ...] = (
    ("can", "you"),
    ("could", "you"),
    ("show", "me"),
    ("tell", "me"),
    ("please",),
)


def normalize_query(text: str) -> str:
    """
    Normalize a raw query string for routing.

    >>> normalize_query("Can you explain force?")
    'explain force'
    >>> normalize_query("show me dependency chain for velocity")
    'dependency chain for velocity'
    """
    text = text.lower()
    text = text.translate(_PUNCT_TABLE)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    tokens = _strip_leading_polite(tokens)
    return " ".join(tokens)


def normalize_tokens(tokens: List[str]) -> List[str]:
    """Strip leading polite-phrase tokens. Used for slot extraction clarity."""
    return _strip_leading_polite([t.lower() for t in tokens])


def _strip_leading_polite(tokens: List[str]) -> List[str]:
    lower = [t.lower() for t in tokens]
    for prefix in _POLITE_PREFIXES:
        n = len(prefix)
        if lower[:n] == list(prefix):
            return tokens[n:]
    return tokens
