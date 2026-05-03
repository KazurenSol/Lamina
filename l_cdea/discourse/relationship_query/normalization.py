"""
Term and relation-type normalization for relationship queries.

normalize_term(term)          → lowercase, strip punct, collapse whitespace
normalize_relation_type(text) → canonical snake_case relation name
"""
from __future__ import annotations

import re
import string

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)

_RELATION_MAP = {
    "depend on":   "depends_on",
    "depends on":  "depends_on",
    "depend":      "depends_on",
    "depends":     "depends_on",
    "related to":  "related_to",
    "related":     "related_to",
    "causes":      "causes",
    "cause":       "causes",
    "part of":     "part_of",
    "part":        "part_of",
    "is a":        "is_a",
    "is":          "is_a",
}


def normalize_term(term: str) -> str:
    term = term.strip().lower()
    term = term.translate(_PUNCT_TABLE)
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def normalize_relation_type(text: str) -> str:
    """Map a natural-language relation phrase to a canonical relation name."""
    key = text.strip().lower()
    key = re.sub(r"\s+", " ", key)
    return _RELATION_MAP.get(key, key.replace(" ", "_"))
