"""
Group consecutive TaggedSentences into coherent chunks.

Splitting policy (conservative — prefer longer groups over fragmentation):

  SPLIT when:
    (a) Hard boundary: sentence is in a different paragraph.
    (b) New definition: sentence introduces "X is/means ..." where X differs
        from the current group's established subject (first-token comparison).

  KEEP (continuation) when:
    - Pronoun start: It, Its, This, That, They, He, She, We, These, Those, ...
    - Connective start: Therefore, However, Because, For example, ...
    - Question: sentence ends with '?'
    - Default: no split signal fires.

Pronoun check runs before the definition-subject check so that
"It is a vector quantity." is never treated as a new subject "It".
"""
from __future__ import annotations

import re
from typing import List, Optional

from l_cdea.ingestion.semantic_chunker.sentence_splitter import TaggedSentence

_PRONOUNS = frozenset({
    "it", "its", "this", "that", "these", "those",
    "they", "their", "them", "he", "his", "she", "her",
    "we", "our", "us", "such", "both", "each", "which",
})

_CONNECTIVES = (
    "therefore", "however", "because", "since", "thus", "hence",
    "moreover", "furthermore", "in addition", "for example", "for instance",
    "as a result", "consequently", "nevertheless", "specifically",
    "that is", "in other words", "so ", "but ", "and ", "or ", "also ",
    "additionally", "likewise", "nonetheless", "instead", "otherwise",
    "indeed", "in fact", "of course", "naturally", "meaning ",
)

_DEF_RE = re.compile(
    r'^(.+?)\s+(?:is|means|refers to|is defined as|is known as)\s+',
    re.IGNORECASE,
)


def _subject(text: str) -> Optional[str]:
    m = _DEF_RE.match(text)
    if not m:
        return None
    return m.group(1).strip().split()[0].lower().strip(".,;:!?()")


def _is_pronoun_start(text: str) -> bool:
    first = text.split()[0].lower().rstrip(".,;:!?()") if text.split() else ""
    return first in _PRONOUNS


def _is_connective_start(text: str) -> bool:
    lower = text.lower().strip()
    return any(lower.startswith(c) for c in _CONNECTIVES)


class SentenceGroup:
    def __init__(self, first: TaggedSentence) -> None:
        self.sentences: List[TaggedSentence] = [first]
        self.paragraph_index: int = first.paragraph_index
        self.subject: Optional[str] = _subject(first.text)

    def add(self, sentence: TaggedSentence) -> None:
        self.sentences.append(sentence)
        if self.subject is None:
            self.subject = _subject(sentence.text)

    def text(self) -> str:
        return " ".join(s.text for s in self.sentences)


def group_sentences(sentences: List[TaggedSentence]) -> List[SentenceGroup]:
    if not sentences:
        return []

    groups: List[SentenceGroup] = []
    current = SentenceGroup(sentences[0])

    for sent in sentences[1:]:
        # Rule 1: hard boundary
        if sent.paragraph_index != current.paragraph_index:
            groups.append(current)
            current = SentenceGroup(sent)
            continue

        # Rule 2: pronoun — always continue
        if _is_pronoun_start(sent.text):
            current.add(sent)
            continue

        # Rule 3: connective — always continue
        if _is_connective_start(sent.text):
            current.add(sent)
            continue

        # Rule 4: question — always continue
        if sent.text.rstrip().endswith("?"):
            current.add(sent)
            continue

        # Rule 5: new definition subject — split
        new_subj = _subject(sent.text)
        if new_subj is not None and current.subject is not None:
            if new_subj != current.subject:
                groups.append(current)
                current = SentenceGroup(sent)
                continue

        # Default: keep
        current.add(sent)

    groups.append(current)
    return groups
