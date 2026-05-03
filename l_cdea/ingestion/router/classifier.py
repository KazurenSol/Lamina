"""
classify_chunk(text) → IngestionRoute

Steps:
  1. normalize text (lowercase, strip)
  2. match all PatternRules (keyword hits + structure hit)
  3. score per category: sum(keyword_hits + structure_hit + priority) across matched rules
  4. select highest-scoring category
  5. tie → mark ambiguous, break by lexicographic category name
  6. no match → category="unknown", fallback=True

Confidence:
  min(1.0, raw_score / MAX_CONFIDENCE_DIVISOR)
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from l_cdea.ingestion.router.patterns import ALL_RULES, PatternRule
from l_cdea.ingestion.router.route import IngestionRoute, make_route_id

MAX_CONFIDENCE_DIVISOR = 10  # score ≥ 10 → confidence 1.0


def _normalize(text: str) -> str:
    return text.lower().strip()


def _keyword_hits(rule: PatternRule, normalized_text: str) -> int:
    """Count how many of the rule's keyword phrases appear in the text."""
    count = 0
    for phrase in rule.keywords:
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, normalized_text, re.IGNORECASE):
            count += 1
    return count


def _structure_hit(rule: PatternRule, normalized_text: str) -> int:
    """Return 1 if the rule's compiled structure matches, 0 otherwise."""
    compiled = rule.compiled_structure()
    if compiled is None:
        return 0
    return 1 if compiled.search(normalized_text) else 0


def classify_chunk(text: str, index: int = 0, mode: str = "document") -> IngestionRoute:
    """Classify a single text chunk into a semantic category."""
    normalized = _normalize(text)
    route_id = make_route_id(text, index)

    # Per-category: accumulated score and matched rule IDs
    category_scores: Dict[str, int] = defaultdict(int)
    category_patterns: Dict[str, List[str]] = defaultdict(list)

    for rule in ALL_RULES:
        kw = _keyword_hits(rule, normalized)
        st = _structure_hit(rule, normalized)
        if kw == 0 and st == 0:
            continue
        hit_score = kw + st + rule.priority
        category_scores[rule.category] += hit_score
        category_patterns[rule.category].append(rule.id)

    # In dictionary mode, boost the definition category to ensure it wins
    # over claim/example when the content matches definition patterns.
    if mode == "dictionary":
        from l_cdea.ingestion.modes.config import get_mode_config
        boost = get_mode_config(mode).definition_priority_boost
        if boost and "definition" in category_scores:
            category_scores["definition"] += boost

    if not category_scores:
        return IngestionRoute(
            route_id=route_id,
            chunk_text=text,
            category="unknown",
            confidence=0.0,
            matched_patterns=(),
            fallback=True,
        )

    max_score = max(category_scores.values())
    winners = sorted(
        [cat for cat, sc in category_scores.items() if sc == max_score]
    )
    ambiguous = len(winners) > 1
    selected = winners[0]  # lexicographic tiebreak

    all_matched = tuple(
        pid
        for cat in category_patterns
        for pid in category_patterns[cat]
    )
    confidence = min(1.0, max_score / MAX_CONFIDENCE_DIVISOR)

    return IngestionRoute(
        route_id=route_id,
        chunk_text=text,
        category=selected,
        confidence=confidence,
        matched_patterns=all_matched,
        fallback=False,
    )


def classify_chunks(
    texts: Tuple[str, ...] | List[str],
    mode: str = "document",
) -> Tuple[IngestionRoute, ...]:
    """Classify a sequence of chunks; detect cross-chunk ambiguity."""
    return tuple(classify_chunk(t, i, mode=mode) for i, t in enumerate(texts))
