from dataclasses import dataclass
from typing import List

from l_cdea.execution.engine import ExecutionBundle
from .state import DiscourseState, create_empty
from .node import DiscourseNode
from .edge import DiscourseEdge
from .temporal import TemporalEvent
from .importer import import_bundle
from .memory_graph import get_node, get_nodes_by_type, get_edges_by_relation
from .exceptions import (
    DiscourseError, DiscourseImportError, SalienceError, MemoryGraphError,
    PersistenceError, SchemaVersionError,
)
from .storage import save_state, load_state, snapshot_id, state_to_snapshot, snapshot_to_state
from .definition_retrieval import (
    register_definition,
    lookup_definition,
    clear_definitions,
    DefinitionEntry,
    DefinitionLookupResult,
    DefinitionRetrievalTrace,
    normalize_term,
)
from .definition_retrieval.operator import register_discourse_operators, register_governed_operators as _register_discourse_governed
from .relationship_query.operator import register_discourse_operators as _register_rel_operators, register_governed_operators as _register_rel_governed
from .multi_hop_reasoning.operator import register_discourse_operators as _register_mh_operators, register_governed_operators as _register_mh_governed
from .composition_reasoning.operator import register_discourse_operators as _register_cr_operators, register_governed_operators as _register_cr_governed
from .provenance import (
    Provenance,
    ProvenancedValue,
    ProvenanceMergeResult,
    ProvenanceTrace,
    ProvenanceValidationError,
    attach_provenance,
    merge_provenance,
    validate_provenance,
    make_trace_id,
)


@dataclass
class DiscourseUpdateResult:
    """Output of a single discourse update cycle."""
    state: DiscourseState
    added_nodes: List[DiscourseNode]
    added_edges: List[DiscourseEdge]
    reinforced_nodes: List[DiscourseNode]
    temporal_events: List[TemporalEvent]


def update_discourse(bundle: ExecutionBundle, state: DiscourseState) -> DiscourseUpdateResult:
    """
    Import execution results into DiscourseState.
    Called only after full execution completes — no streaming updates.
    Returns a result object; the state is updated in-place.
    """
    added, reinforced, edges, events = import_bundle(bundle, state)
    return DiscourseUpdateResult(
        state=state,
        added_nodes=added,
        added_edges=edges,
        reinforced_nodes=reinforced,
        temporal_events=events,
    )


def create_discourse_state() -> DiscourseState:
    return create_empty()


# Bootstrap discourse operators into CDL registry + governance
register_discourse_operators()
try:
    _register_discourse_governed()
except Exception:
    pass

_register_rel_operators()
try:
    _register_rel_governed()
except Exception:
    pass

_register_mh_operators()
try:
    _register_mh_governed()
except Exception:
    pass

_register_cr_operators()
try:
    _register_cr_governed()
except Exception:
    pass


__all__ = [
    "update_discourse",
    "create_discourse_state",
    "DiscourseUpdateResult",
    "DiscourseState",
    "DiscourseNode",
    "DiscourseEdge",
    "TemporalEvent",
    "DiscourseError",
    "DiscourseImportError",
    "SalienceError",
    "MemoryGraphError",
    "PersistenceError",
    "SchemaVersionError",
    "save_state",
    "load_state",
    "snapshot_id",
    "state_to_snapshot",
    "snapshot_to_state",
    "Provenance",
    "ProvenancedValue",
    "ProvenanceMergeResult",
    "ProvenanceTrace",
    "ProvenanceValidationError",
    "attach_provenance",
    "merge_provenance",
    "validate_provenance",
    "make_trace_id",
    "register_definition",
    "lookup_definition",
    "clear_definitions",
    "DefinitionEntry",
    "DefinitionLookupResult",
    "DefinitionRetrievalTrace",
    "normalize_term",
]
