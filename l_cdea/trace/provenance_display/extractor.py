"""
extract_provenance_from_node(node)      → Tuple[DisplayedProvenance, ...]
extract_provenance_for_term(term, state) → Tuple[DisplayedProvenance, ...]
extract_provenance_from_lookup_traces(traces, value) → Tuple[DisplayedProvenance, ...]

Rules:
  - Deduplicate by trace_id.
  - Sort: confidence DESC → timestamp_index DESC → trace_id ASC (deterministic).
  - Never raise — degrade to empty tuple on any error.
  - Never mutate stored provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class DisplayedProvenance:
    source_path: Optional[str]
    chunk_id: Optional[str]
    location: Optional[str]
    extraction_method: str
    confidence: float
    trace_id: str
    source_id: Optional[str] = None      # dataset name or document title


def extract_provenance_from_node(node) -> Tuple[DisplayedProvenance, ...]:
    """Extract DisplayedProvenance from a DiscourseNode."""
    try:
        raw = getattr(node, "provenance", None) or ()
        return _from_provenance_objects(raw)
    except Exception:
        return ()


def extract_provenance_for_term(
    term: str,
    state,
    max_entries: int = 3,
) -> Tuple[DisplayedProvenance, ...]:
    """
    Look up the definition node for `term` in `state` and return its provenance.
    Falls back to an empty tuple if the term is not found.
    """
    try:
        from l_cdea.discourse.definition_retrieval.lookup import lookup_definition
        result = lookup_definition(term, state)
        if not result.hit:
            return ()
        if result.matched_node_id and hasattr(state, "nodes"):
            node = state.nodes.get(result.matched_node_id)
            if node is not None:
                return extract_provenance_from_node(node)[:max_entries]
        return ()
    except Exception:
        return ()


def extract_relationship_provenance(
    relationship_result,
    max_entries: int = 3,
) -> Tuple[DisplayedProvenance, ...]:
    """
    Extract DisplayedProvenance from a RelationshipResult's per-edge provenance.
    Deduplicates by trace_id, sorts by confidence DESC, limits to max_entries.
    """
    try:
        prov = getattr(relationship_result, "provenance", None) or ()
        return _from_provenance_objects(prov)[:max_entries]
    except Exception:
        return ()


def extract_provenance_from_lookup_traces(
    traces,
    value: str,
) -> Tuple[DisplayedProvenance, ...]:
    """
    Build DisplayedProvenance from data-lookup traces whose returned_value
    matches `value`. Used for dataset-backed results (e.g. capital lookups).
    """
    try:
        entries: List[DisplayedProvenance] = []
        seen: set = set()
        for t in (traces or []):
            if not t.hit:
                continue
            if str(t.returned_value) != str(value):
                continue
            prov_dict = t.provenance or {}
            trace_id = prov_dict.get("trace_id", f"lt_{t.dataset_name}_{t.lookup_key}")
            if trace_id in seen:
                continue
            seen.add(trace_id)
            entries.append(DisplayedProvenance(
                source_path=prov_dict.get("source_path"),
                chunk_id=prov_dict.get("chunk_id"),
                location=prov_dict.get("location"),
                extraction_method=prov_dict.get("extraction_method", "dataset_lookup"),
                confidence=float(prov_dict.get("confidence", 1.0)),
                trace_id=trace_id,
                source_id=prov_dict.get("source_id", t.dataset_name),
            ))
        return _sort(entries)
    except Exception:
        return ()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _from_provenance_objects(provs) -> Tuple[DisplayedProvenance, ...]:
    seen: set = set()
    entries: List[DisplayedProvenance] = []
    for p in provs:
        tid = getattr(p, "trace_id", None) or ""
        if tid in seen:
            continue
        seen.add(tid)
        entries.append(DisplayedProvenance(
            source_path=getattr(p, "source_path", None),
            chunk_id=getattr(p, "chunk_id", None),
            location=getattr(p, "location", None),
            extraction_method=getattr(p, "extraction_method", "unknown"),
            confidence=float(getattr(p, "confidence", 0.0)),
            trace_id=tid,
            source_id=getattr(p, "source_id", None),
        ))
    return _sort(entries)


def _sort(entries: List[DisplayedProvenance]) -> Tuple[DisplayedProvenance, ...]:
    """confidence DESC → trace_id ASC (deterministic tie-break)."""
    return tuple(sorted(entries, key=lambda e: (-e.confidence, e.trace_id)))
