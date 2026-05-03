"""
L-CDEA Trace module — deterministic observability for the full pipeline.

Public API:
    TraceLogger          — create one per query; call record_*() at each stage
    TraceRecord          — immutable snapshot of a complete pipeline run
    TraceEvent           — single stage observation within a record
    InMemoryTraceSink    — accumulates records in memory (for tests)
    JSONLTraceSink       — appends one JSON line per record to a file
    to_dict / to_json / to_pretty_text — formatting helpers
    extract_replay_metadata / replay_summary — V1 replay support
"""
from l_cdea.trace.event import (
    TraceEvent,
    TraceRecord,
    TraceSink,
    STAGE_PARSE,
    STAGE_ROUTER,
    STAGE_PLANNER,
    STAGE_COMPILER,
    STAGE_CANONICALIZER,
    STAGE_MECP,
    STAGE_EXECUTION,
    STAGE_DATA_LOOKUP,
    STAGE_DISCOURSE,
    STAGE_PERSISTENCE,
    STAGE_PROVENANCE,
    STAGE_ERROR,
    make_trace_id,
    make_event_id,
)
from l_cdea.trace.logger import TraceLogger
from l_cdea.trace.sinks import InMemoryTraceSink, JSONLTraceSink
from l_cdea.trace.formatter import to_dict, to_json, to_pretty_text
from l_cdea.trace.replay import extract_replay_metadata, replay_summary

__all__ = [
    # Core types
    "TraceEvent",
    "TraceRecord",
    "TraceSink",
    # Logger
    "TraceLogger",
    # Sinks
    "InMemoryTraceSink",
    "JSONLTraceSink",
    # Formatters
    "to_dict",
    "to_json",
    "to_pretty_text",
    # Replay
    "extract_replay_metadata",
    "replay_summary",
    # Stage constants
    "STAGE_PARSE",
    "STAGE_ROUTER",
    "STAGE_PLANNER",
    "STAGE_COMPILER",
    "STAGE_CANONICALIZER",
    "STAGE_MECP",
    "STAGE_EXECUTION",
    "STAGE_DATA_LOOKUP",
    "STAGE_DISCOURSE",
    "STAGE_PERSISTENCE",
    "STAGE_PROVENANCE",
    "STAGE_ERROR",
    # ID helpers
    "make_trace_id",
    "make_event_id",
]
