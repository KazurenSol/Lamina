"""
Deterministic pattern rules for relationship extraction. V1: regex only, no ML.

Patterns are tried in priority order (most specific first). The first match wins.
Each pattern produces one or more (source_term, relation_type, target_term) tuples.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Return type: list of (source, relation_type, target) raw string triples.
MatchResult = List[Tuple[str, str, str]]


@dataclass(frozen=True)
class Pattern:
    name: str
    regex: re.Pattern
    relation_type: str

    def match(self, text: str) -> Optional[MatchResult]:
        raise NotImplementedError


@dataclass(frozen=True)
class SingleTargetPattern(Pattern):
    """Extracts one (source, relation, target) triple."""

    def match(self, text: str) -> Optional[MatchResult]:
        m = self.regex.match(text.strip())
        if not m:
            return None
        return [(m.group(1).strip(), self.relation_type, m.group(2).strip())]


@dataclass(frozen=True)
class MultiTargetPattern(Pattern):
    """Extracts multiple (source, relation, targetN) triples from one match."""

    def match(self, text: str) -> Optional[MatchResult]:
        m = self.regex.match(text.strip())
        if not m:
            return None
        source = m.group(1).strip()
        targets = [g.strip() for g in m.groups()[1:] if g and g.strip()]
        return [(source, self.relation_type, t) for t in targets]


# ── Pattern definitions (most specific first) ─────────────────────────────────

# 1. "X is Y times Z" → X depends_on Y, X depends_on Z
_TIMES = MultiTargetPattern(
    name="is_times",
    relation_type="depends_on",
    regex=re.compile(
        r"^(.+?)\s+is\s+(.+?)\s+times\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 2. "X is the rate of change of Y" → X depends_on Y
_RATE_OF_CHANGE = SingleTargetPattern(
    name="rate_of_change",
    relation_type="depends_on",
    regex=re.compile(
        r"^(.+?)\s+is\s+the\s+rate\s+of\s+change\s+of\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 3. "X consists of Y and Z" → X depends_on Y, X depends_on Z
_CONSISTS_OF = MultiTargetPattern(
    name="consists_of",
    relation_type="depends_on",
    regex=re.compile(
        r"^(.+?)\s+consists?\s+of\s+(.+?)\s+and\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 4. "X is defined as Y" / "X is known as Y" → X is_a Y
_DEFINED_AS = SingleTargetPattern(
    name="defined_as",
    relation_type="is_a",
    regex=re.compile(
        r"^(.+?)\s+is\s+(?:defined|known)\s+as\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 5. "X uses Y" → X depends_on Y
_USES = SingleTargetPattern(
    name="uses",
    relation_type="depends_on",
    regex=re.compile(
        r"^(.+?)\s+uses?\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 6. "X is a Y" / "X is an Y" → X is_a Y  (article form, before plain "is")
_IS_A = SingleTargetPattern(
    name="is_a_article",
    relation_type="is_a",
    regex=re.compile(
        r"^(.+?)\s+is\s+an?\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# 7. "X is Y" → X is_a Y  (plain copula, lowest priority)
_IS = SingleTargetPattern(
    name="is_plain",
    relation_type="is_a",
    regex=re.compile(
        r"^(.+?)\s+is\s+(.+?)\.?$",
        re.IGNORECASE,
    ),
)

# Ordered list — first match wins.
ALL_PATTERNS: Tuple[Pattern, ...] = (
    _TIMES,
    _RATE_OF_CHANGE,
    _CONSISTS_OF,
    _DEFINED_AS,
    _USES,
    _IS_A,
    _IS,
)
