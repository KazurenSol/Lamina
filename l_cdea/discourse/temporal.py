from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .state import DiscourseState


@dataclass
class TemporalEvent:
    """Records what happened at a single temporal index step."""
    index: int
    event_type: str     # "add_node", "reinforce_node", "add_edge", "failure"
    node_ids: List[str] = field(default_factory=list)
    metadata: str = ""


def advance_index(state: DiscourseState) -> int:
    """Increment the temporal index and return the new value."""
    state.temporal_index += 1
    return state.temporal_index


def record_event(
    events: List[TemporalEvent],
    index: int,
    event_type: str,
    node_ids: List[str],
    metadata: str = "",
) -> TemporalEvent:
    evt = TemporalEvent(index=index, event_type=event_type, node_ids=node_ids, metadata=metadata)
    events.append(evt)
    return evt
