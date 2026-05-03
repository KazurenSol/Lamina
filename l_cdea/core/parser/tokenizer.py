from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .exceptions import TokenizationError

_PATTERN = re.compile(r"\w+(?:'\w+)?|[^\w\s]")


@dataclass(frozen=True)
class Token:
    """Raw text segment with character-level position. No semantic content."""
    form: str
    start: int
    end: int


TokenStream = List[Token]


def tokenize(text: str) -> TokenStream:
    """
    Split raw text into positional tokens.
    Splits at word/non-word boundaries; discards pure whitespace.
    No normalization, no interpretation.
    """
    if not isinstance(text, str):
        raise TokenizationError(f"Expected str input, got {type(text).__name__}")
    tokens: TokenStream = []
    for match in _PATTERN.finditer(text):
        tokens.append(Token(form=match.group(), start=match.start(), end=match.end()))
    return tokens
