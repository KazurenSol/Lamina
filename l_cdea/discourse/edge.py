from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiscourseEdge:
    source_id: str
    target_id: str
    relation_type: str
    salience: float
    provenance: tuple = field(default_factory=tuple)  # Tuple[Provenance, ...]
