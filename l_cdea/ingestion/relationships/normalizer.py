"""
Term normalization for relationship extraction.

normalize_term(term) applies: lowercase, strip punctuation, strip leading
articles, trim and collapse whitespace. No stemming in V1.
"""
from __future__ import annotations

import re
import string

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_LEADING_ARTICLE = re.compile(r"^(?:a|an|the)\s+", re.IGNORECASE)


def normalize_term(term: str) -> str:
    term = term.strip()
    term = term.lower()
    term = term.translate(_PUNCT_TABLE)
    term = _LEADING_ARTICLE.sub("", term)
    term = re.sub(r"\s+", " ", term)
    return term.strip()
