"""
Persistent DiscourseState storage.

save_state(state, path)  → writes JSON snapshot, returns PersistentDiscourseSnapshot
load_state(path)         → reads JSON snapshot, returns DiscourseState
                           also restores the planner result cache so Layer-1
                           cache hits work immediately across process boundaries.

snapshot_id(state)       → deterministic hash of snapshot content
state_to_snapshot(state) → PersistentDiscourseSnapshot (no I/O)
snapshot_to_state(snap)  → DiscourseState (no I/O)

Determinism rules:
- sort_keys=True on all JSON writes
- nodes sorted by id
- edges sorted by (source_id, target_id, relation_type)
- temporal events preserve insertion order
- snapshot_id = sha256 of the full JSON body (without snapshot_id field)
- save same state twice → identical file bytes
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from l_cdea.core.types.base import SemanticType, TypedValue
from l_cdea.discourse.state import DiscourseState, create_empty
from l_cdea.discourse.node import DiscourseNode
from l_cdea.discourse.edge import DiscourseEdge
from l_cdea.discourse.temporal import TemporalEvent
from l_cdea.discourse.memory_graph import add_node, add_edge
from l_cdea.discourse.schema import (
    SCHEMA_VERSION, CREATED_BY,
    PersistentDiscourseSnapshot,
    SerializedDiscourseNode, SerializedDiscourseEdge, SerializedTemporalEvent,
)
from l_cdea.discourse.exceptions import DiscourseError, PersistenceError, SchemaVersionError


# ── Public API ─────────────────────────────────────────────────────────────────

def save_state(state: DiscourseState, path: str) -> PersistentDiscourseSnapshot:
    """
    Serialize state to a JSON file at path.
    Also writes the planner result cache into snapshot metadata so it survives
    process boundaries.
    Raises PersistenceError on write failure. Never overwrites on failure.
    """
    snap = state_to_snapshot(state)
    _write_snapshot(snap, path)
    return snap


def load_state(path: str) -> DiscourseState:
    """
    Load DiscourseState from a JSON file.
    Also restores the planner result cache (Layer-1 in-session cache) from
    snapshot metadata, validating each entry against the loaded DiscourseState.
    DiscourseState is the authoritative layer — entries that contradict it are
    reconciled to the discourse value before being written to the cache.

    - Missing file   → empty DiscourseState, no crash
    - Corrupt JSON   → PersistenceError
    - Wrong version  → SchemaVersionError
    """
    if not os.path.exists(path):
        return create_empty()

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise PersistenceError(f"Corrupt state file at '{path}': {exc}") from exc
    except OSError as exc:
        raise PersistenceError(f"Cannot read state file '{path}': {exc}") from exc

    version = raw.get("schema_version", "")
    if version != SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Unsupported schema version '{version}' (expected '{SCHEMA_VERSION}')"
        )

    snap = _dict_to_snapshot(raw)
    state = snapshot_to_state(snap)

    # Rebuild _DEFINITION_STORE from definition nodes in loaded state.
    _restore_definition_store(state)

    # Restore planner cache, cross-checking each entry against DiscourseState.
    # DiscourseState is authoritative: entries that disagree are reconciled.
    _restore_planner_cache(snap.metadata.get("planner_cache", {}), state)

    return state


def snapshot_id(state: DiscourseState) -> str:
    """Compute a deterministic ID for the current state without creating a full snapshot."""
    snap = state_to_snapshot(state)
    return snap.snapshot_id


def state_to_snapshot(state: DiscourseState) -> PersistentDiscourseSnapshot:
    """Convert DiscourseState → PersistentDiscourseSnapshot (no I/O)."""
    nodes = sorted(
        [_serialize_node(n) for n in state.nodes.values()],
        key=lambda n: n.id,
    )
    edges = sorted(
        [_serialize_edge(e) for e in state.edges],
        key=lambda e: (e.source_id, e.target_id, e.relation_type),
    )
    # temporal_index is an int on DiscourseState — no stored events list at state level
    temporal: List[SerializedTemporalEvent] = []

    planner_cache = _capture_planner_cache()
    meta = {
        "temporal_index": state.temporal_index,
        "salience_index": dict(sorted(state.salience_index.items())),
        "planner_cache": planner_cache,
    }

    body = _compute_body(nodes, edges, temporal, meta)
    sid = _hash_body(body)

    return PersistentDiscourseSnapshot(
        schema_version=SCHEMA_VERSION,
        created_by=CREATED_BY,
        snapshot_id=sid,
        nodes=nodes,
        edges=edges,
        temporal_index=temporal,
        metadata=meta,
    )


def snapshot_to_state(snap: PersistentDiscourseSnapshot) -> DiscourseState:
    """Convert PersistentDiscourseSnapshot → DiscourseState (no I/O)."""
    state = create_empty()
    state.temporal_index = snap.metadata.get("temporal_index", 0)

    for sn in snap.nodes:
        node = _deserialize_node(sn)
        add_node(state, node)

    for se in snap.edges:
        edge = _deserialize_edge(se)
        add_edge(state, edge)

    # Restore salience_index from metadata (overrides the one set by add_node)
    saved_salience = snap.metadata.get("salience_index", {})
    if saved_salience:
        state.salience_index.update(saved_salience)

    return state


# ── Serialization helpers ─────────────────────────────────────────────────────

def _serialize_node(n: DiscourseNode) -> SerializedDiscourseNode:
    from l_cdea.discourse.provenance.model import provenance_to_dict
    return SerializedDiscourseNode(
        id=n.id,
        semantic_type=n.semantic_type.value,
        value=_to_json_value(n.value),
        salience=n.salience,
        created_at=n.created_at,
        updated_at=n.updated_at,
        provenance=[provenance_to_dict(p) for p in (n.provenance or ())],
        metadata=dict(n.metadata) if n.metadata else {},
    )


def _deserialize_node(sn: SerializedDiscourseNode) -> DiscourseNode:
    from l_cdea.discourse.provenance.model import provenance_from_dict
    provs = tuple(
        provenance_from_dict(d)
        for d in (sn.provenance or [])
        if isinstance(d, dict)
    )
    return DiscourseNode(
        id=sn.id,
        semantic_type=SemanticType(sn.semantic_type),
        value=sn.value,
        salience=sn.salience,
        created_at=sn.created_at,
        updated_at=sn.updated_at,
        provenance=provs,
        metadata=dict(sn.metadata) if sn.metadata else {},
    )


def _serialize_edge(e: DiscourseEdge) -> SerializedDiscourseEdge:
    from l_cdea.discourse.provenance.model import provenance_to_dict
    return SerializedDiscourseEdge(
        source_id=e.source_id,
        target_id=e.target_id,
        relation_type=e.relation_type,
        salience=e.salience,
        provenance=[provenance_to_dict(p) for p in (e.provenance or ())],
    )


def _deserialize_edge(se: SerializedDiscourseEdge) -> DiscourseEdge:
    from l_cdea.discourse.provenance.model import provenance_from_dict
    prov_raw = se.provenance
    if isinstance(prov_raw, dict):
        prov_raw = []   # backward compat: old files stored provenance as {}
    provs = tuple(
        provenance_from_dict(d) for d in prov_raw if isinstance(d, dict)
    )
    return DiscourseEdge(
        source_id=se.source_id,
        target_id=se.target_id,
        relation_type=se.relation_type,
        salience=se.salience,
        provenance=provs,
    )


def _to_json_value(v: Any) -> Any:
    """Coerce a node value to a JSON-compatible form. Dicts and scalars pass through."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {str(k): _to_json_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_to_json_value(i) for i in v]
    return str(v)


# ── Planner cache bridge ───────────────────────────────────────────────────────

def _capture_planner_cache() -> Dict[str, Dict]:
    """Serialize the planner in-session result cache for snapshot storage."""
    from l_cdea.core.planner.discourse_lookup import _RESULT_CACHE
    out: Dict[str, Dict] = {}
    for key, tv in _RESULT_CACHE.items():
        out[key] = {
            "value": _to_json_value(tv.value),
            "type": tv.type.value,
        }
    return out


def _restore_planner_cache(cache_data: Dict[str, Dict], state) -> None:
    """
    Restore the planner cache from snapshot metadata, validating each entry
    against the loaded DiscourseState before committing it to _RESULT_CACHE.

    Authority rule: DiscourseState wins on conflict. Unverifiable entries are DROPPED.

      - Deserialization fails → skip the entry.
      - DiscourseState has a node matching the cached value → restore using the
        discourse node as the authoritative source.
      - DiscourseState has NO node matching the cached value → DROP the entry.
        A value not present in DiscourseState cannot be verified as correct.
        It may be tampered, stale, or derived from a now-invalid computation.
        The planner will re-execute on the next query and repopulate the cache.
    """
    from l_cdea.core.planner.discourse_lookup import _RESULT_CACHE
    from l_cdea.discourse.memory_graph import lookup_by_value

    if not state.nodes:
        # Empty DiscourseState (fresh start) — can't verify anything; restore as-is
        for key, entry in cache_data.items():
            try:
                tv = TypedValue(value=entry["value"], type=SemanticType(entry["type"]))
                _RESULT_CACHE[key] = tv
            except Exception:
                continue
        return

    for key, entry in cache_data.items():
        try:
            tv = TypedValue(value=entry["value"], type=SemanticType(entry["type"]))
        except Exception:
            continue  # malformed entry — skip

        # Cross-check against DiscourseState (authoritative layer)
        discourse_node = lookup_by_value(state, tv.value)
        if discourse_node is not None:
            # DiscourseState confirms this value — restore using discourse as source
            authoritative = TypedValue(
                value=discourse_node.value,
                type=discourse_node.semantic_type,
            )
            _RESULT_CACHE[key] = authoritative
        # else: value not in DiscourseState → drop entry (cannot verify, may be tampered)


def _restore_definition_store(state) -> None:
    """Rebuild _DEFINITION_STORE from DiscourseState definition nodes after load."""
    from l_cdea.discourse.definition_retrieval.lookup import register_definition

    for node in state.nodes.values():
        meta = getattr(node, "metadata", {}) or {}
        if meta.get("category") != "definition":
            continue
        term = meta.get("term", "")
        definition_text = meta.get("definition_text", str(node.value))
        if not term or not definition_text:
            continue
        prov_list = getattr(node, "provenance", ()) or ()
        confidence = prov_list[0].confidence if prov_list else 0.8
        source_id = prov_list[0].source_id if prov_list else "unknown"
        register_definition(
            term=term,
            definition_text=definition_text,
            source_id=source_id,
            confidence=confidence,
            timestamp_index=node.updated_at,
            node_id=node.id,
        )


# ── JSON I/O ──────────────────────────────────────────────────────────────────

def _snapshot_to_dict(snap: PersistentDiscourseSnapshot) -> Dict:
    return {
        "schema_version": snap.schema_version,
        "created_by": snap.created_by,
        "snapshot_id": snap.snapshot_id,
        "nodes": [
            {
                "id": n.id,
                "semantic_type": n.semantic_type,
                "value": n.value,
                "salience": n.salience,
                "created_at": n.created_at,
                "updated_at": n.updated_at,
                "provenance": n.provenance,
                "canonical_signature": n.canonical_signature,
                "metadata": n.metadata,
            }
            for n in snap.nodes
        ],
        "edges": [
            {
                "source_id": e.source_id,
                "target_id": e.target_id,
                "relation_type": e.relation_type,
                "salience": e.salience,
                "provenance": e.provenance,
            }
            for e in snap.edges
        ],
        "temporal_index": [
            {
                "index": t.index,
                "event_type": t.event_type,
                "node_ids": t.node_ids,
                "metadata": t.metadata,
            }
            for t in snap.temporal_index
        ],
        "metadata": snap.metadata,
    }


def _dict_to_snapshot(raw: Dict) -> PersistentDiscourseSnapshot:
    nodes = [
        SerializedDiscourseNode(
            id=n["id"],
            semantic_type=n["semantic_type"],
            value=n["value"],
            salience=n["salience"],
            created_at=n["created_at"],
            updated_at=n["updated_at"],
            provenance=n.get("provenance", []),
            canonical_signature=n.get("canonical_signature"),
            metadata=n.get("metadata", {}),
        )
        for n in raw.get("nodes", [])
    ]
    edges = [
        SerializedDiscourseEdge(
            source_id=e["source_id"],
            target_id=e["target_id"],
            relation_type=e["relation_type"],
            salience=e["salience"],
            provenance=e.get("provenance", []),
        )
        for e in raw.get("edges", [])
    ]
    temporal = [
        SerializedTemporalEvent(
            index=t["index"],
            event_type=t["event_type"],
            node_ids=t["node_ids"],
            metadata=t.get("metadata", ""),
        )
        for t in raw.get("temporal_index", [])
    ]
    return PersistentDiscourseSnapshot(
        schema_version=raw["schema_version"],
        created_by=raw.get("created_by", CREATED_BY),
        snapshot_id=raw["snapshot_id"],
        nodes=nodes,
        edges=edges,
        temporal_index=temporal,
        metadata=raw.get("metadata", {}),
    )


def _write_snapshot(snap: PersistentDiscourseSnapshot, path: str) -> None:
    """Write snapshot to path atomically (write to tmp, then rename)."""
    d = _snapshot_to_dict(snap)
    content = json.dumps(d, sort_keys=True, indent=2)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise PersistenceError(f"Failed to write state to '{path}': {exc}") from exc


# ── Snapshot ID ───────────────────────────────────────────────────────────────

def _compute_body(
    nodes: List[SerializedDiscourseNode],
    edges: List[SerializedDiscourseEdge],
    temporal: List[SerializedTemporalEvent],
    meta: Dict,
) -> str:
    """Produce a deterministic string representation of snapshot content."""
    body = {
        "schema_version": SCHEMA_VERSION,
        "nodes": [
            {"id": n.id, "semantic_type": n.semantic_type,
             "value": n.value, "salience": n.salience}
            for n in nodes
        ],
        "edges": [
            {"source_id": e.source_id, "target_id": e.target_id,
             "relation_type": e.relation_type, "salience": e.salience}
            for e in edges
        ],
        "temporal_index": meta.get("temporal_index", 0),
    }
    return json.dumps(body, sort_keys=True)


def _hash_body(body: str) -> str:
    return "snap_" + hashlib.sha256(body.encode()).hexdigest()[:16]
