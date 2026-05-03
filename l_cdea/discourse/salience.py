from __future__ import annotations

from .state import DiscourseState
from .exceptions import SalienceError

DECAY_FACTOR: float = 0.95
MIN_SALIENCE: float = 0.01  # nodes never fully disappear — semantic truth is preserved


def apply_decay(state: DiscourseState) -> None:
    """
    Apply temporal salience decay to all nodes.
    Deterministic: decay_factor is constant.
    Salience never drops to zero — semantic truth is never erased, only deprioritised.
    """
    for node_id, node in state.nodes.items():
        node.salience = max(MIN_SALIENCE, node.salience * DECAY_FACTOR)
        state.salience_index[node_id] = node.salience


def reinforce(state: DiscourseState, node_id: str, amount: float) -> None:
    """Increase salience of an existing node. Used when the same result is seen again."""
    if node_id not in state.nodes:
        raise SalienceError(f"Node '{node_id}' not found in DiscourseState")
    state.nodes[node_id].salience += amount
    state.salience_index[node_id] = state.nodes[node_id].salience
