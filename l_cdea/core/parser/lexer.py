from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, List, Tuple

from .exceptions import LexingError
from .tokenizer import Token, TokenStream


class LexicalTag(Enum):
    WORD = "WORD"
    NUMBER = "NUMBER"
    PUNCT = "PUNCT"
    SYMBOL = "SYMBOL"


@dataclass(frozen=True)
class LexicalUnit:
    """Token annotated with surface-level lexical tags. Ambiguity is preserved — no disambiguation."""
    form: str
    span: Tuple[int, int]
    tags: FrozenSet[LexicalTag]


def lex(token_stream: TokenStream) -> List[LexicalUnit]:
    """Assign lexical tags to each token. No meaning assignment, no ranking."""
    units: List[LexicalUnit] = []
    for token in token_stream:
        try:
            tags = _assign_tags(token.form)
        except Exception as e:
            raise LexingError(f"Failed to lex token '{token.form}': {e}") from e
        units.append(LexicalUnit(form=token.form, span=(token.start, token.end), tags=frozenset(tags)))
    return units


_PUNCT_CHARS = frozenset('.,:;!?()[]{}"\'-')


def _assign_tags(form: str) -> List[LexicalTag]:
    if _is_number(form):
        return [LexicalTag.NUMBER]
    if form.replace("'", "").isalpha():
        return [LexicalTag.WORD]
    if all(c in _PUNCT_CHARS for c in form):
        return [LexicalTag.PUNCT]
    return [LexicalTag.SYMBOL]


def _is_number(form: str) -> bool:
    try:
        float(form)
        return True
    except ValueError:
        return False
