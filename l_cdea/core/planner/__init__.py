"""
Query Planner — bridges RouteResult → executable QueryPlan.

Pipeline position:
  Parser → Router → Planner → (Compiler | direct execution) → CAS → MECP → Execution → Discourse
"""
from __future__ import annotations

from typing import Tuple

from l_cdea.core.router.intent import IntentFrame
from l_cdea.core.router import RouteResult
from l_cdea.discourse.state import DiscourseState
from l_cdea.core.planner.plan import QueryPlan, PlanningError, PlanTrace, DiscourseLookupResult
from l_cdea.core.planner.discourse_lookup import discourse_lookup, cache_result, make_lookup_key
from l_cdea.core.planner.slot_hydrator import hydrate_slots
from l_cdea.core.planner.operator_resolver import resolve_operator, retype_slots_for_operator, slot_key_order
from l_cdea.core.planner.graph_builder import build_graph


def plan(
    route_result: RouteResult,
    state: DiscourseState,
) -> Tuple[QueryPlan, PlanTrace]:
    """
    Main planner entry point. Takes a RouteResult and DiscourseState.
    Returns a QueryPlan (executable or cache-hit) and a PlanTrace for diagnostics.
    """
    intent = route_result.selected_intent
    errors = []
    hydrated: dict = {}
    op_key = f"{intent.domain}.{intent.operator_name}"

    # ── Fallback path ──────────────────────────────────────────────────────
    if intent.fallback:
        qplan = QueryPlan(
            intent=intent,
            cache_hit=False,
            provenance={"pattern_id": intent.source_pattern_id, "fallback": True},
            errors=tuple(errors),
        )
        trace = PlanTrace(
            intent=intent,
            discourse_lookup=None,
            hydrated_slots={},
            operator_key="generic.GENERIC_COMPILE",
            type_validation={},
            graph_nodes=0,
            errors=errors,
        )
        return qplan, trace

    # ── Step 1: Discourse lookup ───────────────────────────────────────────
    lookup_result = discourse_lookup(intent, state)
    if lookup_result.hit:
        qplan = QueryPlan(
            intent=intent,
            cache_hit=True,
            cached_result=lookup_result.value,
            cache_trace={"key": make_lookup_key(intent), "strategy": lookup_result.match_strategy},
            provenance={"pattern_id": intent.source_pattern_id, "domain": intent.domain},
            errors=(),
        )
        trace = PlanTrace(
            intent=intent,
            discourse_lookup=lookup_result,
            hydrated_slots={},
            operator_key=op_key,
            type_validation={"skipped": "cache_hit"},
            graph_nodes=0,
            errors=[],
        )
        return qplan, trace

    # ── Step 1b: Discourse definition retrieval (before graph build) ──────
    if intent.domain == "discourse" and intent.operator_name == "GET_DEFINITION":
        from l_cdea.core.types.base import TypedValue, SemanticType
        from l_cdea.discourse.definition_retrieval.lookup import lookup_definition
        from l_cdea.discourse.definition_retrieval.normalization import normalize_term
        term = intent.slots.get("term", "")
        def_result = lookup_definition(term, state)
        if def_result.hit and def_result.definition_text:
            tv = TypedValue(def_result.definition_text, SemanticType.ENTITY)
            qplan = QueryPlan(
                intent=intent,
                cache_hit=True,
                cached_result=tv,
                cache_trace={
                    "strategy": "definition_retrieval",
                    "term": term,
                    "hit": True,
                    "fallback": False,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_DEFINITION",
                type_validation={"strategy": "definition_node_lookup", "hit": True},
                graph_nodes=0,
                errors=[],
            )
        else:
            tv = TypedValue(f"definition_of({normalize_term(term)})", SemanticType.ENTITY)
            qplan = QueryPlan(
                intent=intent,
                cache_hit=False,
                cached_result=tv,
                cache_trace={
                    "strategy": "definition_retrieval",
                    "term": term,
                    "hit": False,
                    "fallback": True,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_DEFINITION",
                type_validation={"strategy": "definition_node_lookup", "hit": False},
                graph_nodes=0,
                errors=[],
            )
        return qplan, trace

    # ── Step 1c: Discourse relationship query (before graph build) ────────
    if intent.domain == "discourse" and intent.operator_name == "GET_RELATIONSHIPS":
        from l_cdea.core.types.base import TypedValue, SemanticType
        from l_cdea.discourse.relationship_query.lookup import lookup_relationships
        from l_cdea.discourse.relationship_query.normalization import normalize_term
        term = intent.slots.get("term", "")
        relation_type = intent.slots.get("relation_type", "depends_on")
        rel_result, rel_trace = lookup_relationships(term, relation_type, state)
        if rel_result.hit and rel_result.values:
            lines = [f"{normalize_term(term)} {relation_type}:"]
            for v in rel_result.values:
                lines.append(f"  - {v}")
            tv = TypedValue("\n".join(lines), SemanticType.ENTITY)
            qplan = QueryPlan(
                intent=intent,
                cache_hit=True,
                cached_result=tv,
                cache_trace={
                    "strategy": "relationship_query",
                    "term": term,
                    "relation_type": relation_type,
                    "hit": True,
                    "fallback": False,
                    "matched_source_node_id": rel_result.source_node_id,
                    "returned_values": list(rel_result.values),
                    "results": rel_result.results,   # Tuple[RelationshipResult, ...] for provenance display
                    "provenance_count": rel_result.provenance_count,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_RELATIONSHIPS",
                type_validation={"strategy": "relationship_query", "hit": True},
                graph_nodes=0,
                errors=[],
            )
        else:
            tv = TypedValue(
                f"relationships_of({normalize_term(term)}, {relation_type})",
                SemanticType.ENTITY,
            )
            qplan = QueryPlan(
                intent=intent,
                cache_hit=False,
                cached_result=tv,
                cache_trace={
                    "strategy": "relationship_query",
                    "term": term,
                    "relation_type": relation_type,
                    "hit": False,
                    "fallback": True,
                    "returned_values": [],
                    "provenance_count": 0,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_RELATIONSHIPS",
                type_validation={"strategy": "relationship_query", "hit": False},
                graph_nodes=0,
                errors=[],
            )
        return qplan, trace

    # ── Step 1d: Multi-hop closure (before graph build) ───────────────────
    if intent.domain == "discourse" and intent.operator_name == "GET_RELATIONSHIP_CLOSURE":
        from l_cdea.core.types.base import TypedValue, SemanticType
        from l_cdea.discourse.multi_hop_reasoning.traversal import compute_closure
        from l_cdea.discourse.relationship_query.normalization import normalize_term
        term = intent.slots.get("term", "")
        relation_type = intent.slots.get("relation_type", "depends_on")
        try:
            max_depth = int(intent.slots.get("max_depth", "3"))
        except (ValueError, TypeError):
            max_depth = 3
        closure_result, mh_trace = compute_closure(term, relation_type, state, max_depth)
        if not closure_result.fallback_used and closure_result.paths:
            lines = [f"{normalize_term(term)} ultimately {relation_type}:"]
            for p in closure_result.paths:
                lines.append(f"  - {p.target}")
                lines.append(f"    path: {' → '.join(p.path)}")
            tv = TypedValue("\n".join(lines), SemanticType.ENTITY)
            qplan = QueryPlan(
                intent=intent,
                cache_hit=True,
                cached_result=tv,
                cache_trace={
                    "strategy": "multi_hop_closure",
                    "term": term,
                    "relation_type": relation_type,
                    "max_depth": max_depth,
                    "hit": True,
                    "fallback": False,
                    "closure_result": closure_result,
                    "cycle_detected": mh_trace.cycle_detected,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_RELATIONSHIP_CLOSURE",
                type_validation={"strategy": "multi_hop_closure", "hit": True},
                graph_nodes=0,
                errors=[],
            )
        else:
            tv = TypedValue(
                f"closure_of({normalize_term(term)}, {relation_type})",
                SemanticType.ENTITY,
            )
            qplan = QueryPlan(
                intent=intent,
                cache_hit=False,
                cached_result=tv,
                cache_trace={
                    "strategy": "multi_hop_closure",
                    "term": term,
                    "relation_type": relation_type,
                    "max_depth": max_depth,
                    "hit": False,
                    "fallback": True,
                    "closure_result": closure_result,
                    "cycle_detected": mh_trace.cycle_detected,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.GET_RELATIONSHIP_CLOSURE",
                type_validation={"strategy": "multi_hop_closure", "hit": False},
                graph_nodes=0,
                errors=[],
            )
        return qplan, trace

    # ── Step 1e: Composition reasoning (before graph build) ───────────────
    if intent.domain == "discourse" and intent.operator_name == "COMPOSE_RELATIONSHIPS":
        from l_cdea.core.types.base import TypedValue, SemanticType
        from l_cdea.discourse.composition_reasoning.composer import compose
        from l_cdea.discourse.relationship_query.normalization import normalize_term
        term = intent.slots.get("term", "")
        relation_type = intent.slots.get("relation_type", "depends_on")
        try:
            max_depth = int(intent.slots.get("max_depth", "3"))
        except (ValueError, TypeError):
            max_depth = 3
        comp_result, comp_trace = compose(term, relation_type, state, max_depth)
        if not comp_result.fallback_used:
            lines = [f"{normalize_term(term)} dependencies:"]
            if comp_result.direct:
                lines.append("Direct:")
                for cr in comp_result.direct:
                    lines.append(f"  - {cr.target}")
            if comp_result.indirect:
                lines.append("Indirect:")
                for cr in comp_result.indirect:
                    lines.append(f"  - {cr.target}")
            tv = TypedValue("\n".join(lines), SemanticType.ENTITY)
            qplan = QueryPlan(
                intent=intent,
                cache_hit=True,
                cached_result=tv,
                cache_trace={
                    "strategy": "composition_reasoning",
                    "term": term,
                    "relation_type": relation_type,
                    "max_depth": max_depth,
                    "hit": True,
                    "fallback": False,
                    "comp_result": comp_result,
                    "cycle_detected": False,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.COMPOSE_RELATIONSHIPS",
                type_validation={"strategy": "composition_reasoning", "hit": True},
                graph_nodes=0,
                errors=[],
            )
        else:
            tv = TypedValue(
                f"compose_of({normalize_term(term)}, {relation_type})",
                SemanticType.ENTITY,
            )
            qplan = QueryPlan(
                intent=intent,
                cache_hit=False,
                cached_result=tv,
                cache_trace={
                    "strategy": "composition_reasoning",
                    "term": term,
                    "relation_type": relation_type,
                    "max_depth": max_depth,
                    "hit": False,
                    "fallback": True,
                    "comp_result": comp_result,
                    "cycle_detected": False,
                },
                provenance={"pattern_id": intent.source_pattern_id, "domain": "discourse"},
                errors=(),
            )
            trace = PlanTrace(
                intent=intent,
                discourse_lookup=lookup_result,
                hydrated_slots={},
                operator_key="discourse.COMPOSE_RELATIONSHIPS",
                type_validation={"strategy": "composition_reasoning", "hit": False},
                graph_nodes=0,
                errors=[],
            )
        return qplan, trace

    # ── Step 2: Slot hydration ─────────────────────────────────────────────
    hydrated, hydration_err = hydrate_slots(intent.domain, intent.slots)
    if hydration_err:
        errors.append(hydration_err)
        qplan = QueryPlan(
            intent=intent, cache_hit=False,
            provenance={"pattern_id": intent.source_pattern_id},
            errors=tuple(errors),
        )
        trace = PlanTrace(intent=intent, discourse_lookup=lookup_result,
                          hydrated_slots={}, operator_key=op_key,
                          type_validation={}, graph_nodes=0, errors=errors)
        return qplan, trace

    # ── Step 3: Operator resolution ───────────────────────────────────────
    resolve_result = resolve_operator(intent.domain, intent.operator_name, hydrated)
    op, resolve_err, gov_trace = resolve_result
    if resolve_err:
        errors.append(resolve_err)
        qplan = QueryPlan(
            intent=intent, cache_hit=False, hydrated_slots=hydrated,
            provenance={"pattern_id": intent.source_pattern_id},
            errors=tuple(errors),
        )
        trace = PlanTrace(intent=intent, discourse_lookup=lookup_result,
                          hydrated_slots=hydrated, operator_key=op_key,
                          type_validation={"error": resolve_err.code},
                          graph_nodes=0, errors=errors,
                          operator_governance_trace=gov_trace)
        return qplan, trace

    # ── Step 3b: Retype slots to match operator TypeSignature ─────────────
    # arg_order is () for V1 rules (alphabetical); non-empty for V2 rules.
    # Capture order and retyped dict for the trace before overwriting hydrated.
    _slot_order = tuple(slot_key_order(hydrated, intent.arg_order))
    retyped = retype_slots_for_operator(op, hydrated, intent.arg_order)
    hydrated = retyped
    _op_sig = {
        "input_types": [t.value for t in op.signature.input_types],
        "output_type": op.signature.output_type.value,
    }

    # ── Step 4: Graph construction ─────────────────────────────────────────
    graph, build_err = build_graph(op, hydrated, intent.arg_order)
    if build_err:
        errors.append(build_err)
        qplan = QueryPlan(
            intent=intent, cache_hit=False, operator=op, hydrated_slots=hydrated,
            provenance={"pattern_id": intent.source_pattern_id},
            errors=tuple(errors),
        )
        trace = PlanTrace(intent=intent, discourse_lookup=lookup_result,
                          hydrated_slots=hydrated, operator_key=op_key,
                          type_validation={"passed": True},
                          graph_nodes=0, errors=errors,
                          slot_order_used=_slot_order, retyped_slots=retyped,
                          operator_signature=_op_sig,
                          operator_governance_trace=gov_trace)
        return qplan, trace

    # ── Step 5: Successful plan ────────────────────────────────────────────
    qplan = QueryPlan(
        intent=intent,
        cache_hit=False,
        operator=op,
        hydrated_slots=hydrated,
        graph=graph,
        provenance={
            "pattern_id": intent.source_pattern_id,
            "domain": intent.domain,
            "operator": op_key,
            "slots": intent.slots,
        },
        errors=(),
    )
    trace = PlanTrace(
        intent=intent,
        discourse_lookup=lookup_result,
        hydrated_slots=hydrated,
        operator_key=op_key,
        type_validation={"passed": True, "arity": len(hydrated)},
        graph_nodes=len(graph.nodes),
        errors=[],
        slot_order_used=_slot_order,
        retyped_slots=retyped,
        operator_signature=_op_sig,
        operator_governance_trace=gov_trace,
    )
    return qplan, trace


__all__ = [
    "plan",
    "QueryPlan",
    "PlanningError",
    "PlanTrace",
    "cache_result",
    "make_lookup_key",
]
