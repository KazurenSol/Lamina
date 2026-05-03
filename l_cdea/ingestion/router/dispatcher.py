"""
dispatch(routes) → Dict[str, Tuple[IngestionRoute, ...]]

Groups routes by category so each extractor receives its assigned chunks.
The dispatcher does NOT perform extraction.

Extractor keys:
  "definition"  → definition extractor
  "claim"       → claim extractor
  "procedure"   → procedure extractor
  "example"     → example extractor
  "formula"     → formula extractor
  "unknown"     → generic extractor (or skip)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from l_cdea.ingestion.router.route import IngestionRoute, IngestionRouteResult

EXTRACTOR_KEYS = frozenset({
    "definition", "claim", "procedure", "example", "formula", "unknown",
})


def dispatch(
    result: IngestionRouteResult,
) -> Dict[str, Tuple[IngestionRoute, ...]]:
    """
    Partition routes by category into extractor buckets.
    Returns a dict keyed by category; missing categories are absent (not empty tuples).
    """
    buckets: Dict[str, List[IngestionRoute]] = defaultdict(list)
    for route in result.routes:
        buckets[route.category].append(route)
    return {cat: tuple(routes) for cat, routes in buckets.items()}


def dispatch_routes(
    routes: Tuple[IngestionRoute, ...],
) -> Dict[str, Tuple[IngestionRoute, ...]]:
    """Convenience: dispatch from a bare tuple of routes."""
    return dispatch(IngestionRouteResult(routes=routes, ambiguous=False))
