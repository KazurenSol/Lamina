"""
Provenance types for the discourse layer.

Provenance — immutable record of where a value came from.
ProvenancedValue — a value bundled with its provenance.
ProvenanceMergeResult — outcome of merging two provenance records.
ProvenanceTrace — observability record for provenance events.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

VALID_SOURCE_TYPES = frozenset({"document", "dataset", "execution"})


@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_type: str              # "document" | "dataset" | "execution"
    extraction_method: str        # "definition_extractor", "dataset_lookup", operator name, …
    confidence: float             # [0.0, 1.0]
    trace_id: str
    timestamp_index: int          # monotonic index from DiscourseState
    source_path: Optional[str] = None
    chunk_id: Optional[str] = None
    location: Optional[str] = None


@dataclass(frozen=True)
class ProvenancedValue:
    """A value annotated with its provenance."""
    value: Any
    semantic_type: str
    provenance: Provenance


@dataclass(frozen=True)
class ProvenanceMergeResult:
    merged_provenance: Tuple[Provenance, ...]
    conflict: bool


@dataclass
class ProvenanceTrace:
    """Observability record for provenance attachment and merge events."""
    value: Any
    provenance_entries: Tuple[Provenance, ...]
    merge_events: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_trace_id(source_id: str, extraction_method: str, timestamp_index: int) -> str:
    """Deterministic trace ID from source metadata."""
    content = f"{source_id}:{extraction_method}:{timestamp_index}"
    return "tr_" + hashlib.sha256(content.encode()).hexdigest()[:12]


def provenance_to_dict(p: Provenance) -> Dict:
    return {
        "source_id": p.source_id,
        "source_type": p.source_type,
        "source_path": p.source_path,
        "chunk_id": p.chunk_id,
        "location": p.location,
        "extraction_method": p.extraction_method,
        "confidence": p.confidence,
        "trace_id": p.trace_id,
        "timestamp_index": p.timestamp_index,
    }


def provenance_from_dict(d: Dict) -> Provenance:
    return Provenance(
        source_id=d["source_id"],
        source_type=d["source_type"],
        extraction_method=d["extraction_method"],
        confidence=float(d["confidence"]),
        trace_id=d["trace_id"],
        timestamp_index=int(d["timestamp_index"]),
        source_path=d.get("source_path"),
        chunk_id=d.get("chunk_id"),
        location=d.get("location"),
    )
