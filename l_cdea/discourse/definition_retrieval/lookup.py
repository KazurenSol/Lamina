"""
lookup_definition(term, state=None) → DefinitionLookupResult

Search order:
  1. Exact normalized term match in _DEFINITION_STORE
  2. DiscourseState nodes tagged with metadata.category == "definition"
  3. No match → LookupMiss (hit=False)

Ranking when multiple definitions match:
  1. highest provenance confidence
  2. highest salience (DiscourseState nodes)
  3. newest timestamp_index
  4. deterministic node_id tie-break (lexicographic)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from l_cdea.discourse.definition_retrieval.normalization import normalize_term

# ── In-memory definition store ────────────────────────────────────────────────

@dataclass
class DefinitionEntry:
    term: str
    normalized_term: str
    definition_text: str
    source_id: str
    confidence: float
    timestamp_index: int = 0
    node_id: Optional[str] = None


_DEFINITION_STORE: List[DefinitionEntry] = []


def register_definition(
    term: str,
    definition_text: str,
    source_id: str = "ingestion",
    confidence: float = 0.8,
    timestamp_index: int = 0,
    node_id: Optional[str] = None,
) -> DefinitionEntry:
    """Add a definition to the module-level store. Idempotent by normalized term + source."""
    normalized = normalize_term(term)
    for entry in _DEFINITION_STORE:
        if entry.normalized_term == normalized and entry.source_id == source_id:
            return entry  # already present — no duplicate
    entry = DefinitionEntry(
        term=term,
        normalized_term=normalized,
        definition_text=definition_text,
        source_id=source_id,
        confidence=confidence,
        timestamp_index=timestamp_index,
        node_id=node_id,
    )
    _DEFINITION_STORE.append(entry)
    return entry


def clear_definitions() -> None:
    """Reset the store (for testing)."""
    _DEFINITION_STORE.clear()


# ── Lookup result ─────────────────────────────────────────────────────────────

@dataclass
class DefinitionLookupResult:
    hit: bool
    term: str
    normalized_term: str
    definition_text: Optional[str]
    matched_node_id: Optional[str]
    confidence: float
    provenance_count: int
    fallback_used: bool


# ── Main lookup ───────────────────────────────────────────────────────────────

def lookup_definition(
    term: str,
    state=None,              # Optional[DiscourseState]
) -> DefinitionLookupResult:
    """
    Look up a definition by term.

    Checks:
      1. Module-level _DEFINITION_STORE (populated by ingestion)
      2. DiscourseState nodes tagged with metadata.category == "definition"
    """
    normalized = normalize_term(term)
    candidates: List[_Candidate] = []

    # 1. Module-level store
    for entry in _DEFINITION_STORE:
        if entry.normalized_term == normalized:
            candidates.append(_Candidate(
                definition_text=entry.definition_text,
                node_id=entry.node_id,
                confidence=entry.confidence,
                salience=1.0,
                timestamp_index=entry.timestamp_index,
            ))

    # 2. DiscourseState definition nodes
    if state is not None and hasattr(state, "nodes"):
        for node in state.nodes.values():
            meta = getattr(node, "metadata", {}) or {}
            if meta.get("category") != "definition":
                continue
            node_norm = normalize_term(meta.get("term", ""))
            if node_norm != normalized:
                continue
            prov_count = len(getattr(node, "provenance", ()))
            conf = node.provenance[0].confidence if prov_count > 0 else 0.5
            candidates.append(_Candidate(
                definition_text=meta.get("definition_text", str(node.value)),
                node_id=node.id,
                confidence=conf,
                salience=getattr(node, "salience", 1.0),
                timestamp_index=node.updated_at,
            ))

    if not candidates:
        return DefinitionLookupResult(
            hit=False, term=term, normalized_term=normalized,
            definition_text=None, matched_node_id=None,
            confidence=0.0, provenance_count=0, fallback_used=True,
        )

    # Rank: confidence DESC, salience DESC, timestamp DESC, node_id ASC (tie-break)
    best = sorted(
        candidates,
        key=lambda c: (-c.confidence, -c.salience, -c.timestamp_index, c.node_id or ""),
    )[0]

    prov_count = sum(
        len(getattr(state.nodes[c.node_id], "provenance", ()))
        for c in candidates
        if c.node_id and state is not None and c.node_id in getattr(state, "nodes", {})
    )

    return DefinitionLookupResult(
        hit=True,
        term=term,
        normalized_term=normalized,
        definition_text=best.definition_text,
        matched_node_id=best.node_id,
        confidence=best.confidence,
        provenance_count=prov_count,
        fallback_used=False,
    )


@dataclass
class _Candidate:
    definition_text: str
    node_id: Optional[str]
    confidence: float
    salience: float
    timestamp_index: int
