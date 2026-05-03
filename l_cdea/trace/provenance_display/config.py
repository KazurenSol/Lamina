"""ProvenanceDisplayConfig — controls how provenance is shown in output."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenanceDisplayConfig:
    enabled: bool = True
    max_entries: int = 3
    show_trace_id: bool = False
    show_confidence: bool = True


DEFAULT_CONFIG = ProvenanceDisplayConfig()
