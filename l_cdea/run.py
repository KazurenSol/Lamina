import os

from l_cdea.core.parser import parse
from l_cdea.core.router import route_with_trace
from l_cdea.core.planner import plan, cache_result
from l_cdea.core.planner.graph_builder import execute_plan_graph
from l_cdea.core.compiler import compile
from l_cdea.normalization.canonicalizer import canonicalize
from l_cdea.control.mecp import run_mecp
from l_cdea.execution import run_execution
from l_cdea.discourse import (
    update_discourse, create_discourse_state,
    save_state, load_state, snapshot_id,
    PersistenceError,
)
from l_cdea.trace import TraceLogger, InMemoryTraceSink, to_pretty_text
from l_cdea.data.lookup import get_all_lookup_traces, clear_lookup_trace
from l_cdea.trace.provenance_display import (
    ProvenanceDisplayConfig, DEFAULT_CONFIG as _DEFAULT_PROV_CONFIG,
    extract_provenance_for_term, extract_provenance_from_lookup_traces,
    extract_relationship_provenance,
    format_provenance_lines, format_provenance_inline, format_provenance_no_source,
)

DEFAULT_STATE_PATH = ".l_cdea/discourse_state.json"


class _PathProvAdapter:
    """Thin adapter so extract_relationship_provenance can read path-aggregated provenance."""
    def __init__(self, provenance: tuple) -> None:
        self.provenance = provenance

_state = None          # populated by _init_state()
_state_path = DEFAULT_STATE_PATH
_trace_sink = InMemoryTraceSink()
_state_loaded = False
_snap_id_before = ""
_prov_config: ProvenanceDisplayConfig = _DEFAULT_PROV_CONFIG


def _init_state(path: str) -> None:
    global _state, _state_path, _state_loaded, _snap_id_before
    _state_path = path
    try:
        _state = load_state(path)
        _state_loaded = os.path.exists(path)
        _snap_id_before = snapshot_id(_state)
    except PersistenceError as exc:
        raise  # propagate corrupt-file errors; do not silently start empty


def _save_state_safe(logger: TraceLogger, snap_before: str, nodes_before: int, edges_before: int) -> None:
    """Save state and record persistence trace. Never raises."""
    saved = False
    snap_after = snap_before
    nodes_after = len(_state.nodes)
    edges_after = len(_state.edges)
    try:
        snap = save_state(_state, _state_path)
        snap_after = snap.snapshot_id
        saved = True
    except PersistenceError:
        pass

    logger.record_persistence(
        state_path=_state_path,
        state_loaded=_state_loaded,
        state_saved=saved,
        snapshot_id_before=snap_before,
        snapshot_id_after=snap_after,
        node_count_before=nodes_before,
        node_count_after=nodes_after,
        edge_count_before=edges_before,
        edge_count_after=edges_after,
    )


def run_query(text: str):
    global _state
    print(f"\n=== INPUT ===\n{text}")

    nodes_before = len(_state.nodes)
    edges_before = len(_state.edges)
    snap_before = snapshot_id(_state)

    clear_lookup_trace()
    logger = TraceLogger(text, discourse_snapshot_id=snap_before, sinks=[_trace_sink])

    parsed = parse(text)
    logger.record_parse(parsed)

    route_result, route_trace = route_with_trace(parsed)
    logger.record_router(route_result, route_trace)

    intent = route_result.selected_intent
    qplan, ptrace = plan(route_result, _state)
    logger.record_planner(qplan, ptrace)

    print(f"\n=== INTENT ===")
    if intent.fallback:
        print(f"  (no domain match — generic fallback)")
    else:
        print(f"  domain:    {intent.domain}")
        print(f"  operator:  {intent.operator_name}")
        print(f"  slots:     {intent.slots}")
        print(f"  confidence:{intent.confidence:.3f}")
        if route_result.ambiguous:
            alts = [i.full_operator for i in route_result.intents[1:]]
            print(f"  ambiguous: alternatives = {alts}")

    # ── Cache hit ──────────────────────────────────────────────────────────
    if qplan.cache_hit:
        strategy = qplan.cache_trace.get("strategy", "")
        term = qplan.cache_trace.get("term", "")
        prov_entries = ()

        if strategy == "composition_reasoning":
            comp_result = qplan.cache_trace.get("comp_result")
            print(f"\n=== OUTPUT (composition) ===")
            print(f"  [{qplan.cached_result.type.value}] {term} dependencies:\n")
            if comp_result:
                if comp_result.direct:
                    print("  Direct:")
                    for cr in comp_result.direct:
                        print(f"  - {cr.target}")
                        for path in cr.paths:
                            print(f"    path: {' → '.join(path)}")
                        if _prov_config.enabled:
                            prov_entries = extract_relationship_provenance(
                                _PathProvAdapter(cr.provenance), _prov_config.max_entries
                            )
                            if prov_entries:
                                for line in format_provenance_lines(prov_entries, _prov_config):
                                    print(f"    {line}")
                            else:
                                print(f"    {format_provenance_no_source()}")
                else:
                    print("  Direct: (none)")
                print()
                if comp_result.indirect:
                    print("  Indirect:")
                    for cr in comp_result.indirect:
                        print(f"  - {cr.target}")
                        for path in cr.paths:
                            print(f"    path: {' → '.join(path)}")
                        if _prov_config.enabled:
                            prov_entries = extract_relationship_provenance(
                                _PathProvAdapter(cr.provenance), _prov_config.max_entries
                            )
                            if prov_entries:
                                for line in format_provenance_lines(prov_entries, _prov_config):
                                    print(f"    {line}")
                            else:
                                print(f"    {format_provenance_no_source()}")
                else:
                    print("  Indirect: (none)")
            logger.record_provenance(term, (), fallback=False)
        elif strategy == "multi_hop_closure":
            rel_type = qplan.cache_trace.get("relation_type", "")
            closure_result = qplan.cache_trace.get("closure_result")
            print(f"\n=== OUTPUT (multi-hop) ===")
            print(f"  [{qplan.cached_result.type.value}] {term} ultimately {rel_type}:")
            if closure_result:
                for path in closure_result.paths:
                    print(f"  - {path.target}")
                    print(f"    path: {' → '.join(path.path)}")
                    if _prov_config.enabled:
                        # Show strongest provenance from this path's aggregated entries
                        prov_entries = extract_relationship_provenance(
                            _PathProvAdapter(path.provenance), _prov_config.max_entries
                        )
                        if prov_entries:
                            for line in format_provenance_lines(prov_entries, _prov_config):
                                print(f"    {line}")
                        else:
                            print(f"    {format_provenance_no_source()}")
            logger.record_provenance(term, (), fallback=False)
        elif strategy == "relationship_query":
            rel_type = qplan.cache_trace.get("relation_type", "")
            results = qplan.cache_trace.get("results", ())
            print(f"\n=== OUTPUT (relationships) ===")
            print(f"  [{qplan.cached_result.type.value}] {term} {rel_type}:")
            for rel_res in results:
                print(f"  - {rel_res.target_value}")
                if _prov_config.enabled:
                    prov_entries = extract_relationship_provenance(rel_res, _prov_config.max_entries)
                    if prov_entries:
                        for line in format_provenance_lines(prov_entries, _prov_config):
                            print(f"  {line}")
                    else:
                        print(f"    {format_provenance_no_source()}")
            logger.record_provenance(term, (), fallback=False)
        else:
            print(f"\n=== OUTPUT (cache hit) ===")
            print(f"  [{qplan.cached_result.type.value}] {qplan.cached_result.value}")
            if strategy == "definition_retrieval" and term:
                prov_entries = extract_provenance_for_term(term, _state)
            if _prov_config.enabled:
                if prov_entries:
                    print(format_provenance_inline(prov_entries, _prov_config))
                elif term:
                    print(format_provenance_no_source())
            logger.record_provenance(term, prov_entries)

        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Composition fallback (COMPOSE_RELATIONSHIPS, no paths found) ─────
    if (qplan.cached_result is not None
            and qplan.cache_trace.get("strategy") == "composition_reasoning"
            and qplan.cache_trace.get("fallback") is True):
        term = qplan.cache_trace.get("term", "")
        print(f"\n=== OUTPUT (composition not found) ===")
        print(f"  [{qplan.cached_result.type.value}] {qplan.cached_result.value}")
        if _prov_config.enabled:
            print(format_provenance_no_source())
        logger.record_provenance(term, (), fallback=True)
        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Multi-hop fallback (GET_RELATIONSHIP_CLOSURE, no paths found) ──────
    if (qplan.cached_result is not None
            and qplan.cache_trace.get("strategy") == "multi_hop_closure"
            and qplan.cache_trace.get("fallback") is True):
        term = qplan.cache_trace.get("term", "")
        print(f"\n=== OUTPUT (closure not found) ===")
        print(f"  [{qplan.cached_result.type.value}] {qplan.cached_result.value}")
        if _prov_config.enabled:
            print(format_provenance_no_source())
        logger.record_provenance(term, (), fallback=True)
        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Relationship fallback (GET_RELATIONSHIPS, no edges found) ─────────
    if (qplan.cached_result is not None
            and qplan.cache_trace.get("strategy") == "relationship_query"
            and qplan.cache_trace.get("fallback") is True):
        term = qplan.cache_trace.get("term", "")
        print(f"\n=== OUTPUT (relationships not found) ===")
        print(f"  [{qplan.cached_result.type.value}] {qplan.cached_result.value}")
        if _prov_config.enabled:
            print(format_provenance_no_source())
        logger.record_provenance(term, (), fallback=True)
        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Definition fallback (GET_DEFINITION, term not found in store) ──────
    if (qplan.cached_result is not None
            and qplan.cache_trace.get("strategy") == "definition_retrieval"
            and qplan.cache_trace.get("fallback") is True):
        term = qplan.cache_trace.get("term", "")
        print(f"\n=== OUTPUT (definition not found) ===")
        print(f"  [{qplan.cached_result.type.value}] {qplan.cached_result.value}")
        if _prov_config.enabled:
            print(format_provenance_no_source())
        logger.record_provenance(term, (), fallback=True)
        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Planner errors ─────────────────────────────────────────────────────
    if qplan.errors:
        print(f"\n=== PLANNER ERRORS ===")
        for err in qplan.errors:
            print(f"  [{err.code}] {err.message}")

    # ── Executable plan: run the minimal graph directly ────────────────────
    if qplan.is_executable:
        result = execute_plan_graph(qplan.graph)
        print(f"\n=== OUTPUT ===")
        if result:
            print(f"  [{result.type.value}] {result.value}")
            cache_result(intent, result)
        else:
            print(f"  (operator returned no result)")
        print(f"  graph: {len(qplan.graph.nodes)} nodes  |  operator: {qplan.operator.name}")
        if result and _prov_config.enabled:
            _lookup_traces = get_all_lookup_traces()
            prov_entries = extract_provenance_from_lookup_traces(_lookup_traces, str(result.value))
            if prov_entries:
                print(format_provenance_inline(prov_entries, _prov_config))
            logger.record_provenance(str(result.value), prov_entries)

        class _DirectBundle:
            resolved_graphs = [qplan.graph]
            node_outputs = {"0": result} if result else {}
            success_flags = {"0": result is not None}
            failures = {}

        logger.record_execution(_DirectBundle())
        logger.record_data_lookups(get_all_lookup_traces())

        update = update_discourse(_DirectBundle(), _state)
        logger.record_discourse(update)

        _save_state_safe(logger, snap_before, nodes_before, edges_before)
        logger.finalize("success")
        return qplan

    # ── Fallback: generic compiler path ────────────────────────────────────
    compiled = compile(parsed)
    logger.record_compiler(compiled)

    canon    = canonicalize(compiled)
    logger.record_canonicalizer(canon)

    mecp     = run_mecp(canon)
    logger.record_mecp(mecp)

    bundle   = run_execution(mecp)
    logger.record_execution(bundle)
    logger.record_data_lookups(get_all_lookup_traces())

    update   = update_discourse(bundle, _state)
    logger.record_discourse(update)

    print(f"\n=== OUTPUT (generic) ===")
    if bundle.node_outputs:
        items = list(bundle.node_outputs.items())
        for _, tv in items[:4]:
            print(f"  [{tv.type.value}] {tv.value}")
        if len(items) > 4:
            print(f"  ... ({len(items) - 4} more nodes)")
    else:
        print(f"  (stored as semantic frame)")

    print(f"\n  discourse: +{len(update.added_nodes)} nodes, "
          f"+{len(update.added_edges)} edges, "
          f"{len(update.reinforced_nodes)} reinforced")

    _save_state_safe(logger, snap_before, nodes_before, edges_before)
    logger.finalize("success")
    return qplan


def last_trace():
    """Return the pretty-text trace for the most recently completed query."""
    record = _trace_sink.latest()
    return to_pretty_text(record) if record else "(no trace yet)"


if __name__ == "__main__":
    import sys

    argv = sys.argv[1:]
    show_trace = "--trace" in argv
    no_provenance = "--no-provenance" in argv
    argv = [a for a in argv if a not in ("--trace", "--no-provenance")]

    if no_provenance:
        _prov_config = ProvenanceDisplayConfig(enabled=False)

    # Resolve --state-path
    state_path = DEFAULT_STATE_PATH
    if "--state-path" in argv:
        idx = argv.index("--state-path")
        if idx + 1 < len(argv):
            state_path = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2:]
        else:
            print("Error: --state-path requires a path argument.", file=sys.stderr)
            sys.exit(1)

    # Load persistent state
    try:
        _init_state(state_path)
    except PersistenceError as exc:
        print(f"Error loading state: {exc}", file=sys.stderr)
        sys.exit(1)

    if argv:
        # ── Single-shot CLI mode ───────────────────────────────────────────
        run_query(" ".join(argv))
        if show_trace:
            print(f"\n{last_trace()}")
        sys.exit(0)

    # ── Interactive REPL mode ──────────────────────────────────────────────
    print("L-CDEA — Lamina CDL Discourse Execution Architecture")
    print(f"State: {state_path}  (nodes={len(_state.nodes)}, edges={len(_state.edges)})")
    print("Type a query. Ctrl+C to exit.\n")
    while True:
        try:
            q = input(">>> ").strip()
            if q:
                run_query(q)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
