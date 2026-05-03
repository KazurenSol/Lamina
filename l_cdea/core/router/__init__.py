from __future__ import annotations

from l_cdea.core.parser import ParsedInput
from l_cdea.core.router.intent import IntentFrame, PatternRule, RouteResult, RouteTrace
from l_cdea.core.router.patterns import get_registry, load_domain_patterns, register_rule
from l_cdea.core.router.dispatcher import dispatch

_patterns_loaded = False


def route(parsed: ParsedInput) -> RouteResult:
    """
    Route a ParsedInput to a domain operator intent.
    Loads domain patterns on first call (idempotent thereafter).
    Returns RouteResult with selected_intent and full alternatives list.
    """
    global _patterns_loaded
    if not _patterns_loaded:
        load_domain_patterns()
        _patterns_loaded = True

    result, _trace = dispatch(parsed, get_registry())
    return result


def route_with_trace(parsed: ParsedInput) -> tuple[RouteResult, RouteTrace]:
    """Same as route() but also returns the RouteTrace for debugging."""
    global _patterns_loaded
    if not _patterns_loaded:
        load_domain_patterns()
        _patterns_loaded = True

    return dispatch(parsed, get_registry())


__all__ = [
    "route",
    "route_with_trace",
    "IntentFrame",
    "PatternRule",
    "RouteResult",
    "RouteTrace",
    "register_rule",
    "get_registry",
    "load_domain_patterns",
]
