"""
TraceLogger — the single observer that records pipeline decisions.

Rules:
- MUST NOT mutate any pipeline object.
- MUST NOT raise exceptions from record_*() calls; errors are swallowed so
  the logger never crashes the pipeline.
- record_error() is the only method that sets the failed status path.
- finalize() assembles TraceRecord and fans out to all sinks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from l_cdea.trace.event import (
    TraceEvent, TraceRecord, TraceSink,
    STAGE_PARSE, STAGE_ROUTER, STAGE_PLANNER, STAGE_COMPILER,
    STAGE_CANONICALIZER, STAGE_MECP, STAGE_EXECUTION, STAGE_DATA_LOOKUP,
    STAGE_DISCOURSE, STAGE_PERSISTENCE, STAGE_PROVENANCE, STAGE_ERROR,
    make_trace_id, make_event_id,
)


class TraceLogger:
    """
    Stateful per-query observer. Create one per run_query() call.

    Usage:
        logger = TraceLogger(input_text, discourse_snapshot_id, sinks=[sink])
        logger.record_parse(parsed)
        logger.record_router(route_result, route_trace)
        ...
        record = logger.finalize("success")
    """

    def __init__(
        self,
        input_text: str,
        discourse_snapshot_id: str = "",
        sinks: Optional[List[TraceSink]] = None,
    ) -> None:
        self._input_text = input_text
        self.trace_id = make_trace_id(input_text, discourse_snapshot_id)
        self._events: List[TraceEvent] = []
        self._counter: int = 0
        self._sinks: List[TraceSink] = list(sinks) if sinks else []

    # ── Sink management ────────────────────────────────────────────────────────

    def add_sink(self, sink: TraceSink) -> None:
        self._sinks.append(sink)

    # ── Core recording primitive ───────────────────────────────────────────────

    def record(self, stage: str, payload: Dict[str, Any]) -> TraceEvent:
        event_id = make_event_id(self.trace_id, stage, self._counter)
        event = TraceEvent(
            event_id=event_id,
            stage=stage,
            timestamp_index=self._counter,
            payload=payload,
        )
        self._events.append(event)
        self._counter += 1
        return event

    # ── Stage-specific helpers ─────────────────────────────────────────────────

    def record_parse(self, parsed: Any) -> None:
        try:
            self.record(STAGE_PARSE, {
                "input_text": self._input_text,
                "tokens": [t.form for t in parsed.tokens],
                "lexical_units": [str(lu) for lu in parsed.lexical_units],
                "presemantic_frames": sorted(str(f) for f in parsed.presemantic_frames),
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_PARSE, exc))

    def record_router(self, route_result: Any, route_trace: Any) -> None:
        try:
            intent = route_result.selected_intent
            self.record(STAGE_ROUTER, {
                "matched_patterns": route_trace.matched_patterns,
                "rejected_patterns": route_trace.rejected_patterns,
                "selected_intent": {
                    "domain": intent.domain,
                    "operator_name": intent.operator_name,
                    "slots": dict(intent.slots),
                    "confidence": intent.confidence,
                    "arg_order": list(intent.arg_order),
                    "fallback": intent.fallback,
                },
                "all_intents": [
                    {
                        "domain": i.domain,
                        "operator_name": i.operator_name,
                        "confidence": i.confidence,
                    }
                    for i in route_result.intents
                ],
                "ambiguous": route_result.ambiguous,
                "fallback_used": route_result.fallback_used,
                "confidence_scores": dict(route_trace.confidence_scores),
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_ROUTER, exc))

    def record_planner(self, qplan: Any, ptrace: Any) -> None:
        """
        Planner trace explicitly records slot_order_used to prove
        retype_slots_for_operator() and build_graph() shared the same ordering.
        """
        try:
            intent = qplan.intent
            checked_keys = (
                list(ptrace.discourse_lookup.checked_keys)
                if ptrace.discourse_lookup else []
            )
            self.record(STAGE_PLANNER, {
                "intent": {
                    "domain": intent.domain,
                    "operator_name": intent.operator_name,
                    "slots": dict(intent.slots),
                    "fallback": intent.fallback,
                },
                "cache_checked": True,
                "cache_hit": qplan.cache_hit,
                "cache_keys_checked": checked_keys,
                "hydrated_slots": _serialise_slots(ptrace.hydrated_slots),
                "arg_order": list(intent.arg_order),
                "slot_order_used": list(ptrace.slot_order_used),
                "retyped_slots": _serialise_slots(ptrace.retyped_slots),
                "operator_key": ptrace.operator_key,
                "operator_signature": ptrace.operator_signature,
                "graph_built": ptrace.graph_nodes > 0,
                "planning_errors": [
                    {"code": e.code, "message": e.message}
                    for e in ptrace.errors
                ],
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_PLANNER, exc))

    def record_compiler(self, compiled: Any) -> None:
        try:
            self.record(STAGE_COMPILER, {
                "compiled_graph_count": len(compiled.graphs) if hasattr(compiled, "graphs") else 0,
                "interpretation_count": getattr(compiled, "interpretation_count", 0),
                "binding_count": getattr(compiled, "binding_count", 0),
                "strategy_count": getattr(compiled, "strategy_count", 0),
                "fallback_used": getattr(compiled, "fallback_used", False),
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_COMPILER, exc))

    def record_canonicalizer(self, result: Any) -> None:
        try:
            equiv = {
                str(sig): len(graphs)
                for sig, graphs in result.equivalence_map.items()
            }
            self.record(STAGE_CANONICALIZER, {
                "input_graph_count": len(result.signatures),
                "unique_signature_count": len(set(str(s) for s in result.signatures)),
                "equivalence_classes": equiv,
                "preserved_graph_count": sum(equiv.values()),
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_CANONICALIZER, exc))

    def record_mecp(self, mecp: Any) -> None:
        try:
            self.record(STAGE_MECP, {
                "queue_order": [str(g) for g in mecp.execution_queue],
                "priority_map": {str(k): v for k, v in mecp.priority_map.items()},
                "cost_map": {str(k): v for k, v in mecp.cost_map.items()},
                "gain_map": {str(k): v for k, v in mecp.gain_map.items()},
                "threshold": mecp.threshold_used,
                "selected_graph_count": len(mecp.execution_subset),
                "fallback_used": len(mecp.execution_subset) == 0,
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_MECP, exc))

    def record_execution(self, bundle: Any) -> None:
        try:
            self.record(STAGE_EXECUTION, {
                "graph_order": [str(g) for g in bundle.resolved_graphs],
                "node_execution_order": [],  # V1: not tracked per-node
                "node_inputs": {},            # V1: not tracked per-node
                "node_outputs": {
                    str(k): {"type": v.type.value, "value": str(v.value)}
                    for k, v in bundle.node_outputs.items()
                },
                "success_flags": {str(k): v for k, v in bundle.success_flags.items()},
                "failures": {
                    str(k): [str(e) for e in errs]
                    for k, errs in bundle.failures.items()
                },
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_EXECUTION, exc))

    def record_data_lookups(self, traces: list) -> None:
        """Record all data lookup traces from a single query execution."""
        if not traces:
            return
        try:
            self.record(STAGE_DATA_LOOKUP, {
                "lookups": [
                    {
                        "operator_name": t.operator_name,
                        "dataset_name":  t.dataset_name,
                        "lookup_key":    t.lookup_key,
                        "hit":           t.hit,
                        "returned_value": str(t.returned_value) if t.returned_value is not None else None,
                        "fallback_used": t.fallback_used,
                        "provenance":    t.provenance,
                    }
                    for t in traces
                ],
                "total_lookups": len(traces),
                "hits": sum(1 for t in traces if t.hit),
                "misses": sum(1 for t in traces if not t.hit),
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_DATA_LOOKUP, exc))

    def record_discourse(self, update: Any) -> None:
        try:
            self.record(STAGE_DISCOURSE, {
                "cache_write": bool(update.added_nodes or update.reinforced_nodes),
                "added_nodes": [str(n) for n in update.added_nodes],
                "added_edges": [str(e) for e in update.added_edges],
                "reinforced_nodes": [str(n) for n in update.reinforced_nodes],
                "temporal_events": [str(e) for e in update.temporal_events],
                "salience_updates": {},  # V1: not yet exposed by discourse module
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_DISCOURSE, exc))

    def record_persistence(
        self,
        state_path: str,
        state_loaded: bool,
        state_saved: bool,
        snapshot_id_before: str,
        snapshot_id_after: str,
        node_count_before: int,
        node_count_after: int,
        edge_count_before: int,
        edge_count_after: int,
    ) -> None:
        try:
            self.record(STAGE_PERSISTENCE, {
                "state_path": state_path,
                "state_loaded": state_loaded,
                "state_saved": state_saved,
                "snapshot_id_before": snapshot_id_before,
                "snapshot_id_after": snapshot_id_after,
                "node_count_before": node_count_before,
                "node_count_after": node_count_after,
                "edge_count_before": edge_count_before,
                "edge_count_after": edge_count_after,
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_PERSISTENCE, exc))

    def record_provenance(
        self,
        term: str,
        entries: tuple,
        fallback: bool = False,
    ) -> None:
        """Record provenance entries for a returned value."""
        try:
            self.record(STAGE_PROVENANCE, {
                "term": term,
                "fallback": fallback,
                "entry_count": len(entries),
                "entries": [
                    {
                        "source_path": e.source_path,
                        "chunk_id": e.chunk_id,
                        "location": e.location,
                        "extraction_method": e.extraction_method,
                        "confidence": e.confidence,
                        "trace_id": e.trace_id,
                        "source_id": e.source_id,
                    }
                    for e in entries
                ],
            })
        except Exception as exc:
            self.record(STAGE_ERROR, _err_payload(STAGE_PROVENANCE, exc))

    def record_error(self, stage: str, exc: Exception) -> None:
        self.record(STAGE_ERROR, _err_payload(stage, exc))

    # ── Finalization ───────────────────────────────────────────────────────────

    def finalize(self, status: str = "success") -> TraceRecord:
        """
        Assemble TraceRecord and fan out to all registered sinks.
        Sink errors are swallowed — sinks must never crash the pipeline.
        """
        record = TraceRecord(
            trace_id=self.trace_id,
            input_text=self._input_text,
            events=tuple(self._events),
            final_status=status,
        )
        for sink in self._sinks:
            try:
                sink.write(record)
            except Exception:
                pass
        return record


# ── Internal helpers ───────────────────────────────────────────────────────────

def _err_payload(stage: str, exc: Exception) -> Dict[str, Any]:
    return {
        "stage": stage,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "payload_available": False,
    }


def _serialise_slots(slots: Dict) -> Dict:
    if not slots:
        return {}
    result = {}
    for k, v in slots.items():
        try:
            result[k] = {"type": v.type.value, "value": str(v.value)}
        except Exception:
            result[k] = str(v)
    return result
