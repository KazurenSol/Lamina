"""
V1 replay metadata extraction.

V1 does not re-run the full pipeline — it extracts the minimal set of
inspectable facts from a TraceRecord to support debugging and auditing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from l_cdea.trace.event import (
    TraceRecord,
    STAGE_ROUTER, STAGE_PLANNER, STAGE_EXECUTION,
)


def extract_replay_metadata(record: TraceRecord) -> Dict[str, Any]:
    """
    Extract V1 replay metadata from a completed TraceRecord.

    Returns a dict with:
        original_input          — the raw text fed into the pipeline
        stage_sequence          — ordered list of stage names observed
        selected_intent         — router's winning IntentFrame snapshot
        selected_operator       — planner's resolved operator key
        selected_execution_graph — first graph in execution order (if any)
        final_output            — last node output from EXECUTION stage
    """
    meta: Dict[str, Any] = {
        "original_input": record.input_text,
        "stage_sequence": [e.stage for e in record.events],
        "selected_intent": None,
        "selected_operator": None,
        "selected_execution_graph": None,
        "final_output": None,
        "final_status": record.final_status,
        "trace_id": record.trace_id,
    }

    for e in record.events:
        p = e.payload

        if e.stage == STAGE_ROUTER:
            meta["selected_intent"] = p.get("selected_intent")

        elif e.stage == STAGE_PLANNER:
            meta["selected_operator"] = p.get("operator_key")
            # Also surface slot ordering for auditability
            meta["slot_order_used"] = p.get("slot_order_used")
            meta["arg_order"] = p.get("arg_order")

        elif e.stage == STAGE_EXECUTION:
            graphs = p.get("graph_order", [])
            if graphs:
                meta["selected_execution_graph"] = graphs[0]
            outputs = p.get("node_outputs", {})
            if outputs:
                meta["final_output"] = list(outputs.values())[-1]

    return meta


def replay_summary(record: TraceRecord) -> str:
    """Short human-readable summary of what a trace ran and produced."""
    m = extract_replay_metadata(record)
    intent = m.get("selected_intent") or {}
    lines = [
        f"[{m['trace_id']}] {m['original_input']!r}",
        f"  stages:   {' → '.join(_dedupe_stages(m['stage_sequence']))}",
        f"  intent:   {intent.get('domain', '?')}.{intent.get('operator_name', '?')}",
        f"  operator: {m.get('selected_operator', '—')}",
        f"  output:   {m.get('final_output', '—')}",
        f"  status:   {m['final_status']}",
    ]
    return "\n".join(lines)


def _dedupe_stages(stages: List[str]) -> List[str]:
    """Collapse consecutive duplicates while preserving order."""
    seen: List[str] = []
    for s in stages:
        if not seen or seen[-1] != s:
            seen.append(s)
    return seen
