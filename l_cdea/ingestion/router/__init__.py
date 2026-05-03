"""
l_cdea.ingestion.router — deterministic ingestion routing layer.

Public API:
  classify_chunk(text, index=0) → IngestionRoute
  classify_chunks(texts)        → Tuple[IngestionRoute, ...]
  dispatch(result)              → Dict[str, Tuple[IngestionRoute, ...]]
  dispatch_routes(routes)       → Dict[str, Tuple[IngestionRoute, ...]]

Types:
  IngestionRoute
  IngestionRouteResult
  IngestionRouteTrace
  PatternRule
"""
from l_cdea.ingestion.router.route import (
    IngestionRoute,
    IngestionRouteResult,
    make_route_id,
)
from l_cdea.ingestion.router.patterns import PatternRule, ALL_RULES
from l_cdea.ingestion.router.classifier import classify_chunk, classify_chunks
from l_cdea.ingestion.router.dispatcher import dispatch, dispatch_routes
from l_cdea.ingestion.router.trace import IngestionRouteTrace

__all__ = [
    "IngestionRoute",
    "IngestionRouteResult",
    "IngestionRouteTrace",
    "PatternRule",
    "ALL_RULES",
    "make_route_id",
    "classify_chunk",
    "classify_chunks",
    "dispatch",
    "dispatch_routes",
]
