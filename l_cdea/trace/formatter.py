"""
TraceRecord formatters.

to_dict()        — plain Python dict, JSON-serialisable via default=str.
to_json()        — deterministic JSON string (sort_keys=True).
to_pretty_text() — human-readable summary for REPL / log output.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from l_cdea.trace.event import TraceRecord


def to_dict(record: TraceRecord) -> Dict[str, Any]:
    return {
        "trace_id": record.trace_id,
        "input_text": record.input_text,
        "final_status": record.final_status,
        "events": [
            {
                "event_id": e.event_id,
                "stage": e.stage,
                "timestamp_index": e.timestamp_index,
                "payload": e.payload,
            }
            for e in record.events
        ],
    }


def to_json(record: TraceRecord) -> str:
    return json.dumps(to_dict(record), sort_keys=True, default=str)


def to_pretty_text(record: TraceRecord) -> str:
    lines = [
        f"=== TRACE {record.trace_id} ===",
        f"input:  {record.input_text}",
        f"status: {record.final_status}",
    ]

    for e in record.events:
        lines.append(f"\n[{e.stage}]")
        p = e.payload

        if e.stage == "PARSE":
            lines.append(f"  tokens:  {p.get('tokens')}")

        elif e.stage == "ROUTER":
            intent = p.get("selected_intent", {})
            lines.append(f"  domain:      {intent.get('domain')}")
            lines.append(f"  operator:    {intent.get('operator_name')}")
            lines.append(f"  slots:       {intent.get('slots')}")
            lines.append(f"  arg_order:   {intent.get('arg_order')}")
            lines.append(f"  confidence:  {intent.get('confidence')}")
            lines.append(f"  fallback:    {p.get('fallback_used')}")
            lines.append(f"  ambiguous:   {p.get('ambiguous')}")

        elif e.stage == "PLANNER":
            lines.append(f"  cache_hit:       {p.get('cache_hit')}")
            lines.append(f"  operator:        {p.get('operator_key')}")
            lines.append(f"  arg_order:       {p.get('arg_order')}")
            lines.append(f"  slot_order_used: {p.get('slot_order_used')}")
            lines.append(f"  graph_built:     {p.get('graph_built')}")
            sig = p.get("operator_signature") or {}
            if sig:
                lines.append(f"  signature:       {sig.get('input_types')} → {sig.get('output_type')}")
            errs = p.get("planning_errors", [])
            if errs:
                for err in errs:
                    lines.append(f"  error:           [{err.get('code')}] {err.get('message')}")

        elif e.stage == "COMPILER":
            lines.append(f"  graphs:      {p.get('compiled_graph_count')}")
            lines.append(f"  fallback:    {p.get('fallback_used')}")

        elif e.stage == "CANONICALIZER":
            lines.append(f"  input_graphs:     {p.get('input_graph_count')}")
            lines.append(f"  unique_sigs:      {p.get('unique_signature_count')}")
            lines.append(f"  preserved_graphs: {p.get('preserved_graph_count')}")

        elif e.stage == "MECP":
            lines.append(f"  selected:    {p.get('selected_graph_count')}")
            lines.append(f"  threshold:   {p.get('threshold')}")
            lines.append(f"  fallback:    {p.get('fallback_used')}")

        elif e.stage == "EXECUTION":
            outputs = p.get("node_outputs", {})
            for nid, tv in list(outputs.items())[:4]:
                lines.append(f"  [{tv.get('type')}] {tv.get('value')}")
            if len(outputs) > 4:
                lines.append(f"  ... ({len(outputs) - 4} more nodes)")

        elif e.stage == "DATA_LOOKUP":
            for lk in p.get("lookups", []):
                status = "HIT" if lk.get("hit") else "MISS"
                lines.append(f"  [{status}] {lk.get('dataset_name')} key={lk.get('lookup_key')!r} → {lk.get('returned_value')}")

        elif e.stage == "DISCOURSE":
            lines.append(f"  added_nodes:      {len(p.get('added_nodes', []))}")
            lines.append(f"  added_edges:      {len(p.get('added_edges', []))}")
            lines.append(f"  reinforced_nodes: {len(p.get('reinforced_nodes', []))}")

        elif e.stage == "PERSISTENCE":
            lines.append(f"  state_path:    {p.get('state_path')}")
            lines.append(f"  state_loaded:  {p.get('state_loaded')}")
            lines.append(f"  state_saved:   {p.get('state_saved')}")
            lines.append(f"  snap_before:   {p.get('snapshot_id_before')}")
            lines.append(f"  snap_after:    {p.get('snapshot_id_after')}")
            lines.append(f"  nodes: {p.get('node_count_before')} → {p.get('node_count_after')}")
            lines.append(f"  edges: {p.get('edge_count_before')} → {p.get('edge_count_after')}")

        elif e.stage == "PROVENANCE":
            lines.append(f"  term:    {p.get('term')}")
            if p.get("fallback"):
                lines.append(f"  entries: [no provenance]")
            else:
                for entry in p.get("entries", []):
                    src = entry.get("source_path") or entry.get("source_id") or "—"
                    import os as _os
                    src = _os.path.basename(src) if entry.get("source_path") else src
                    lines.append(
                        f"  - source: {src}"
                        f" | chunk: {entry.get('chunk_id') or '—'}"
                        f" | loc: {entry.get('location') or '—'}"
                        f" | conf: {entry.get('confidence', 0.0):.4f}"
                    )

        elif e.stage == "ERROR":
            lines.append(f"  stage:   {p.get('stage')}")
            lines.append(f"  error:   {p.get('error_type')}: {p.get('error_message')}")

    return "\n".join(lines)
