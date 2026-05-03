from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .node import DiscourseNode
from .edge import DiscourseEdge


@dataclass
class DiscourseState:
    nodes: Dict[str, DiscourseNode] = field(default_factory=dict)
    edges: List[DiscourseEdge] = field(default_factory=list)
    temporal_index: int = 0
    salience_index: Dict[str, float] = field(default_factory=dict)


def create_empty() -> DiscourseState:
    return DiscourseState()
