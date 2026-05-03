"""
normalize_term(term) → str

Rules:
  1. lowercase
  2. strip punctuation (keep word characters and spaces)
  3. trim whitespace
  4. no fuzzy matching in V1
  5. singular/plural normalization: not applied in V1

Examples:
  "Acceleration"  → "acceleration"
  "velocity?"     → "velocity"
  "  Force  "     → "force"
"""
from __future__ import annotations

import re

_PUNCTUATION = re.compile(r"[^\w\s]")


def normalize_term(term: str) -> str:
    result = term.lower()
    result = _PUNCTUATION.sub("", result)
    return result.strip()
