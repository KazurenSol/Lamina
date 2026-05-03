"""
Core trace types: TraceEvent, TraceRecord, TraceSink, stage constants,
and deterministic ID generation.

Hard rules:
- No uuid4 — all IDs are deterministic hashes.
- trace_id  = sha256(input_text + PIPELINE_VERSION + discourse_snapshot_id)[:16]
- event_id  = "{trace_id}:{stage}:{timestamp_index}"
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Tuple

PIPELINE_VERSION = "1.0.0"

# ── Stage constants ────────────────────────────────────────────────────────────
STAGE_PARSE        = "PARSE"
STAGE_ROUTER       = "ROUTER"
STAGE_PLANNER      = "PLANNER"
STAGE_COMPILER     = "COMPILER"
STAGE_CANONICALIZER = "CANONICALIZER"
STAGE_MECP         = "MECP"
STAGE_EXECUTION    = "EXECUTION"
STAGE_DATA_LOOKUP  = "DATA_LOOKUP"
STAGE_DISCOURSE    = "DISCOURSE"
STAGE_PERSISTENCE  = "PERSISTENCE"
STAGE_PROVENANCE   = "PROVENANCE"
STAGE_ERROR        = "ERROR"

ALL_STAGES = (
    STAGE_PARSE, STAGE_ROUTER, STAGE_PLANNER, STAGE_COMPILER,
    STAGE_CANONICALIZER, STAGE_MECP, STAGE_EXECUTION, STAGE_DATA_LOOKUP,
    STAGE_DISCOURSE, STAGE_PERSISTENCE, STAGE_PROVENANCE, STAGE_ERROR,
)


# ── Core types ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TraceEvent:
    """A single observed pipeline decision, immutable after creation."""
    event_id: str
    stage: str
    timestamp_index: int
    payload: Dict


@dataclass(frozen=True)
class TraceRecord:
    """Complete trace for one pipeline run, immutable after finalization."""
    trace_id: str
    input_text: str
    events: Tuple[TraceEvent, ...]
    final_status: str  # "success" | "failed"


class TraceSink:
    """Abstract base for trace output destinations. Subclass and implement write()."""
    name: str = "base"

    def write(self, record: TraceRecord) -> None:
        raise NotImplementedError


# ── ID helpers ─────────────────────────────────────────────────────────────────

def make_trace_id(input_text: str, discourse_snapshot_id: str = "") -> str:
    raw = f"{input_text}:{PIPELINE_VERSION}:{discourse_snapshot_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_event_id(trace_id: str, stage: str, index: int) -> str:
    return f"{trace_id}:{stage}:{index}"
