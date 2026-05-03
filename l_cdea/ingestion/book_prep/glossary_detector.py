"""
detect_glossary_mode(chapter_text) -> GlossaryDetectionResult

Classifies a chapter as glossary_line_mode or paragraph_mode.
All logic is deterministic and rule-based.

Detection rules (all must pass):
  1. valid_lines >= 3
  2. valid_lines / total_lines >= 0.5
  3. average line length <= 120 chars
  4. at least 2 lines match definition/relationship patterns:
       "X is Y"  /  "X is the ..."  /  "X depends on Y"
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from l_cdea.ingestion.modes.filter import is_valid_dictionary_chunk

_IS_PATTERN = re.compile(r"^.{1,60}\s+is\s+", re.IGNORECASE)
_DEPENDS_PATTERN = re.compile(r"^.{1,60}\s+depends\s+on\s+", re.IGNORECASE)

_MIN_VALID_LINES = 3
_MIN_VALID_RATIO = 0.5
_MAX_AVG_LINE_LEN = 120
_MIN_DEF_MATCHES = 2


@dataclass(frozen=True)
class GlossaryDetectionResult:
    glossary_mode: bool
    total_lines: int
    valid_lines: int
    ratio: float


def _matches_def_pattern(line: str) -> bool:
    return bool(_IS_PATTERN.match(line) or _DEPENDS_PATTERN.match(line))


def detect_glossary_mode(chapter_text: str) -> GlossaryDetectionResult:
    """
    Return a GlossaryDetectionResult classifying the chapter as glossary or paragraph.
    Detection is deterministic: same input always produces same result.
    """
    non_empty = [l.strip() for l in chapter_text.splitlines() if l.strip()]
    total_lines = len(non_empty)

    if total_lines == 0:
        return GlossaryDetectionResult(glossary_mode=False, total_lines=0, valid_lines=0, ratio=0.0)

    valid_lines = sum(1 for l in non_empty if is_valid_dictionary_chunk(l))
    avg_len = sum(len(l) for l in non_empty) / total_lines
    def_matches = sum(1 for l in non_empty if _matches_def_pattern(l))
    ratio = valid_lines / total_lines

    glossary_mode = (
        valid_lines >= _MIN_VALID_LINES
        and ratio >= _MIN_VALID_RATIO
        and avg_len <= _MAX_AVG_LINE_LEN
        and def_matches >= _MIN_DEF_MATCHES
    )

    return GlossaryDetectionResult(
        glossary_mode=glossary_mode,
        total_lines=total_lines,
        valid_lines=valid_lines,
        ratio=ratio,
    )
