"""
Split text into sentences, preserving paragraph boundaries.

Each sentence is returned as a TaggedSentence(text, paragraph_index).
Paragraphs are delimited by one or more blank lines.

Rules:
  - Abbreviations (Mr., Dr., i.e., e.g., etc.) do NOT end a sentence.
  - Decimal numbers (3.14, 0.5) do NOT end a sentence.
  - Single uppercase initials (A. Smith) do NOT end a sentence.
  - Sentences end on [.!?] followed by whitespace + uppercase, or end of string.
"""
from __future__ import annotations

import re
from typing import List, NamedTuple

_ABBREVS = frozenset({
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs",
    "etc", "approx", "dept", "est", "fig", "no",
    "st", "ave", "blvd", "corp", "inc", "ltd",
    "i.e", "e.g", "cf", "op", "cit", "vol", "pp",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug",
    "sep", "oct", "nov", "dec",
})

_ABBREV_RE = re.compile(
    r'\b(' + '|'.join(re.escape(a) for a in sorted(_ABBREVS, key=len, reverse=True)) + r')\.',
    re.IGNORECASE,
)
_DECIMAL_RE = re.compile(r'(\d)\.(\d)')
_INITIAL_RE = re.compile(r'\b([A-Z])\.')   # single uppercase letter (initials)

_SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'\(])')

_SAFE = '\x00'


class TaggedSentence(NamedTuple):
    text: str
    paragraph_index: int


def _protect(text: str) -> str:
    text = _ABBREV_RE.sub(lambda m: m.group(1) + _SAFE, text)
    text = _DECIMAL_RE.sub(lambda m: m.group(1) + _SAFE + m.group(2), text)
    text = _INITIAL_RE.sub(lambda m: m.group(1) + _SAFE, text)
    return text


def _restore(text: str) -> str:
    return text.replace(_SAFE, '.')


def split_sentences(text: str) -> List[TaggedSentence]:
    if not text.strip():
        return []

    paragraphs = re.split(r'\n{2,}', text)
    result: List[TaggedSentence] = []

    for para_idx, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue

        protected = _protect(para)
        parts = _SENTENCE_BOUNDARY.split(protected)

        for part in parts:
            sent = _restore(part).strip()
            if sent:
                result.append(TaggedSentence(text=sent, paragraph_index=para_idx))

    return result
