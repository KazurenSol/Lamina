"""
Deterministic pattern dispatcher.
Matches ParsedInput against all registered PatternRules,
scores confidence, handles ambiguity, and returns a RouteResult.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from l_cdea.core.parser import ParsedInput
from l_cdea.core.router.intent import (
    IntentFrame, PatternRule, RouteResult, RouteTrace, FALLBACK_INTENT,
)
from l_cdea.core.router.patterns import PatternRegistry
from l_cdea.core.router.slot_filler import extract_slots


# ---------------------------------------------------------------------------
# Confidence model (deterministic, structural)
# keyword_match_score  : fraction of pattern keywords present in input (0.0–1.0)
# slot_fill_score      : 0.3 if all required slots filled, else 0.0
# priority_bonus       : rule.priority / 1000
# ---------------------------------------------------------------------------

def _score(rule: PatternRule, tokens: List[str], slots_filled: bool) -> float:
    lower_tokens = {t.lower() for t in tokens}
    if not rule.keywords:
        keyword_score = 0.0
    else:
        matched = sum(1 for kw in rule.keywords if kw.lower() in lower_tokens)
        keyword_score = matched / len(rule.keywords)
    slot_score = 0.3 if slots_filled else 0.0
    priority_bonus = rule.priority / 1000.0
    return keyword_score + slot_score + priority_bonus


def _tie_break_key(intent: IntentFrame) -> Tuple:
    """Deterministic tie-breaking: confidence DESC, priority from id, domain, operator, pattern_id."""
    return (
        -intent.confidence,
        intent.domain,
        intent.operator_name,
        intent.source_pattern_id,
    )


def dispatch(parsed: ParsedInput, registry: PatternRegistry) -> Tuple[RouteResult, RouteTrace]:
    # Reconstruct word-token list from ParsedInput.tokens (each Token has a .form field)
    tokens = [t.form for t in parsed.tokens]
    raw_text = " ".join(tokens)

    matched: List[IntentFrame] = []
    rejected: List[str] = []
    confidence_scores: Dict[str, float] = {}

    for rule in registry.all_rules():
        lower_tokens = {t.lower() for t in tokens}
        # Fast keyword pre-filter: all keywords must appear
        if not all(kw.lower() in lower_tokens for kw in rule.keywords):
            rejected.append(rule.id)
            continue

        slots, all_required = extract_slots(
            tokens, rule.required_slots, rule.optional_slots, raw_text
        )
        if not all_required:
            rejected.append(rule.id)
            continue

        conf = _score(rule, tokens, all_required)
        confidence_scores[rule.id] = conf

        matched.append(IntentFrame(
            domain=rule.domain,
            operator_name=rule.operator_name,
            slots=slots,
            confidence=conf,
            source_pattern_id=rule.id,
            fallback=False,
            arg_order=rule.arg_order,
        ))

    if not matched:
        fallback = IntentFrame(
            domain="generic",
            operator_name="GENERIC_COMPILE",
            slots={"raw_text": raw_text},
            confidence=0.0,
            source_pattern_id="fallback.generic",
            fallback=True,
        )
        trace = RouteTrace(
            input_text=raw_text,
            matched_patterns=[],
            rejected_patterns=rejected,
            slot_bindings={"raw_text": raw_text},
            confidence_scores={},
            selected_intent=fallback,
            ambiguous=False,
            fallback_used=True,
        )
        return RouteResult(
            intents=(fallback,),
            selected_intent=fallback,
            ambiguous=False,
            fallback_used=True,
        ), trace

    # Sort: highest confidence first, then deterministic tie-breaking
    matched.sort(key=_tie_break_key)
    selected = matched[0]
    ambiguous = (
        len(matched) > 1
        and matched[1].confidence == selected.confidence
    )

    trace = RouteTrace(
        input_text=raw_text,
        matched_patterns=[i.source_pattern_id for i in matched],
        rejected_patterns=rejected,
        slot_bindings=selected.slots,
        confidence_scores=confidence_scores,
        selected_intent=selected,
        ambiguous=ambiguous,
        fallback_used=False,
    )
    return RouteResult(
        intents=tuple(matched),
        selected_intent=selected,
        ambiguous=ambiguous,
        fallback_used=False,
    ), trace


