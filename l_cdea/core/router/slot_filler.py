"""
Deterministic slot extraction from a token list.

Rules (V1):
1. Slot filling MUST be deterministic.
2. MUST NOT infer unstated facts.
3. MUST preserve raw token values (whitespace/case normalized only).
4. Fails cleanly — returns None for a slot if it cannot be filled.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Positional slot extractors
# ---------------------------------------------------------------------------

def _tokens_after(tokens: List[str], keyword: str, stop_keywords: Tuple[str, ...] = ()) -> Optional[str]:
    """Return all tokens after `keyword` (case-insensitive), stopping at any stop_keyword."""
    lower = [t.lower() for t in tokens]
    try:
        idx = lower.index(keyword.lower())
    except ValueError:
        return None
    rest = tokens[idx + 1:]
    if stop_keywords:
        result = []
        for t in rest:
            if t.lower() in {s.lower() for s in stop_keywords}:
                break
            result.append(t)
        return " ".join(result).strip() or None
    return " ".join(rest).strip() or None


def _token_before(tokens: List[str], keyword: str) -> Optional[str]:
    """Return the single token immediately before `keyword`."""
    lower = [t.lower() for t in tokens]
    try:
        idx = lower.index(keyword.lower())
    except ValueError:
        return None
    return tokens[idx - 1] if idx > 0 else None


def _tokens_between(tokens: List[str], start_kw: str, end_kw: str) -> Optional[str]:
    """Return tokens between two keywords (exclusive)."""
    lower = [t.lower() for t in tokens]
    try:
        i = lower.index(start_kw.lower())
        j = lower.index(end_kw.lower(), i + 1)
    except ValueError:
        return None
    segment = tokens[i + 1:j]
    return " ".join(segment).strip() or None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_slots(
    tokens: List[str],
    required_slots: Tuple[str, ...],
    optional_slots: Tuple[str, ...],
    raw_text: str,
) -> Tuple[Dict[str, str], bool]:
    """
    Attempt to fill required and optional slots from tokens.
    Returns (slot_dict, all_required_filled).

    Slot extraction strategy (V1):
    - "region"      → everything after "of"
    - "expression"  → everything after the operator keyword (first non-keyword token onward)
    - "force"       → tokens between "force" and "and"
    - "mass"        → tokens after "mass"
    - "predicate"   → tokens between "first" and "in"
    - "collection"  → tokens after "in"
    - "amount"      → first numeric token
    - "account"     → token after "into" or "from"
    - "actor"       → first capitalized non-keyword token
    - "action"      → token after "can" or "may" or "must"
    - "rule"        → token after "rule" or "law"
    - Fallback      → last token for single-slot patterns
    """
    slots: Dict[str, str] = {}
    all_slots = list(required_slots) + list(optional_slots)

    for slot in all_slots:
        value = _fill_slot(slot, tokens, raw_text)
        if value is not None:
            slots[slot] = value

    all_required = all(s in slots for s in required_slots)
    return slots, all_required


def _fill_slot(slot: str, tokens: List[str], raw_text: str) -> Optional[str]:
    t = [tok for tok in tokens if tok.lower() not in ("?", ".", ",", "!", ";", ":")]

    if slot == "region":
        return _tokens_after(t, "of")

    if slot == "expression":
        # Everything after the first keyword token (verb-like)
        skip = {"simplify", "expand", "factor", "solve", "calculate", "compute",
                "differentiate", "integrate", "evaluate"}
        for i, tok in enumerate(t):
            if tok.lower() in skip:
                rest = " ".join(t[i + 1:]).strip()
                return rest or None
        return " ".join(t[1:]).strip() or None

    if slot == "variable":
        # Token after "with respect to" or after "for"
        v = _tokens_after(t, "to") or _tokens_after(t, "for")
        return v.split()[0] if v else (t[-1] if t else None)

    if slot == "force":
        return _tokens_between(t, "force", "and") or _tokens_after(t, "force", ("and", "mass"))

    if slot == "mass":
        return _tokens_after(t, "mass") or _tokens_after(t, "weight")

    if slot == "time":
        return _tokens_after(t, "time") or _tokens_after(t, "after") or _tokens_after(t, "for")

    if slot == "predicate":
        return _tokens_between(t, "first", "in")

    if slot == "collection":
        return _tokens_after(t, "in")

    if slot == "amount":
        for tok in t:
            if re.match(r"^\d+(\.\d+)?$", tok):
                return tok
        return None

    if slot == "account":
        return _tokens_after(t, "into") or _tokens_after(t, "from") or _tokens_after(t, "account")

    if slot == "principal":
        # First numeric token
        for tok in t:
            if re.match(r"^\d+(\.\d+)?$", tok):
                return tok
        return None

    if slot == "rate":
        # Token after "rate" or "at" containing %
        after = _tokens_after(t, "rate") or _tokens_after(t, "at")
        if after:
            return after.split()[0]
        return None

    if slot == "actor":
        # First capitalized token that isn't a stop word
        stop = {"the", "a", "an", "is", "was", "are", "were", "be"}
        for tok in t:
            if tok[0].isupper() and tok.lower() not in stop:
                return tok
        return t[0] if t else None

    if slot == "action":
        return _tokens_after(t, "can") or _tokens_after(t, "may") or _tokens_after(t, "must")

    if slot == "rule":
        return _tokens_after(t, "rule") or _tokens_after(t, "law") or _tokens_after(t, "under")

    if slot == "case":
        return _tokens_after(t, "case") or raw_text

    if slot == "substance":
        return _tokens_after(t, "of") or " ".join(t[1:]) or None

    if slot == "max_depth":
        # V1: constant default; future patterns may embed numeric depth in keywords
        return "3"

    if slot == "relation_type":
        from l_cdea.discourse.relationship_query.normalization import normalize_relation_type
        lower = {tok.lower() for tok in tokens}
        if "depend" in lower or "depends" in lower or "dependencies" in lower or "dependency" in lower:
            return "depends_on"
        # Paraphrase synonyms for depends_on
        if ("affects" in lower or "affect" in lower
                or "influences" in lower or "influence" in lower
                or "determines" in lower or "determine" in lower
                or "relies" in lower or "rely" in lower
                or "based" in lower):
            return "depends_on"
        if "related" in lower:
            return "related_to"
        if "causes" in lower or "cause" in lower:
            return "causes"
        if "part" in lower:
            return "part_of"
        return None

    if slot == "term":
        # Remove question/definition/relationship/multi-hop/paraphrase keywords
        skip = {"what", "is", "a", "an", "are", "define", "definition", "of",
                "does", "mean", "?", "the",
                "depend", "depends", "on", "related", "part", "causes", "cause", "to",
                "ultimately", "indirectly", "indirect", "all", "dependencies", "dependency",
                "chain", "show", "for", "derive",
                # paraphrase aux words
                "explain", "tell", "about", "give",
                "affects", "affect", "influences", "influence",
                "based", "determines", "determine", "relies", "rely",
                "full", "graph", "derived",
                # polite-prefix words
                "me", "please", "can", "you", "could"}
        filtered = [tok for tok in t if tok.lower() not in skip]
        return " ".join(filtered).strip() or None

    if slot == "raw_text":
        return raw_text

    # Generic fallback: last meaningful token
    return t[-1] if t else None
