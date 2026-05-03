"""
Persistent discourse schema — version constants and serialization types.

Rules:
- SCHEMA_VERSION must be bumped on any breaking change to the snapshot format.
- All serialized types are plain dicts so they round-trip through JSON without
  custom decoders.
- Do NOT add wall-clock timestamps to snapshot identity fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Schema 1.1: SerializedDiscourseNode.provenance changed from Dict to List[Dict]
# Schema 1.2: SerializedDiscourseNode.metadata added (Dict, default {})

SCHEMA_VERSION = "1.2"
CREATED_BY = "l_cdea"


@dataclass
class SerializedDiscourseNode:
    id: str
    semantic_type: str          # SemanticType.value (string)
    value: Any                  # JSON-compatible; complex types stored as str
    salience: float
    created_at: int
    updated_at: int
    provenance: List[Dict] = field(default_factory=list)
    canonical_signature: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class SerializedDiscourseEdge:
    source_id: str
    target_id: str
    relation_type: str
    salience: float
    provenance: List[Dict] = field(default_factory=list)


@dataclass
class SerializedTemporalEvent:
    index: int
    event_type: str
    node_ids: List[str]
    metadata: str = ""


@dataclass
class PersistentDiscourseSnapshot:
    schema_version: str
    created_by: str
    snapshot_id: str
    nodes: List[SerializedDiscourseNode]
    edges: List[SerializedDiscourseEdge]
    temporal_index: List[SerializedTemporalEvent]
    metadata: Dict = field(default_factory=dict)
