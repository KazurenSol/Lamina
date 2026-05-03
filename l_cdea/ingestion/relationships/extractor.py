"""
extract_relationships(chunk_text, metadata, provenance) → RelationshipExtractionResult

Steps:
1. Split chunk into sentences.
2. For each sentence, try patterns in priority order.
3. Normalize extracted terms.
4. Build RelationshipEdge(s) with attached provenance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from l_cdea.discourse.provenance.model import Provenance
from l_cdea.ingestion.relationships.normalizer import normalize_term
from l_cdea.ingestion.relationships.patterns import ALL_PATTERNS
from l_cdea.ingestion.relationships.trace import RelationshipTrace

_MIN_TERM_LEN = 2        # ignore single-char noise terms
_CONFIDENCE_DEFAULT = 0.75


@dataclass(frozen=True)
class RelationshipEdge:
    source_term: str      # normalized
    relation_type: str
    target_term: str      # normalized
    confidence: float
    provenance: Provenance


@dataclass(frozen=True)
class RelationshipExtractionResult:
    edges: Tuple[RelationshipEdge, ...]
    traces: Tuple[RelationshipTrace, ...]


def extract_relationships(
    chunk_text: str,
    provenance: Provenance,
    confidence: float = _CONFIDENCE_DEFAULT,
) -> RelationshipExtractionResult:
    """
    Extract relationship edges from a chunk of text.
    Deterministic: same input always produces same output.
    """
    sentences = _split_sentences(chunk_text)
    all_edges: List[RelationshipEdge] = []
    all_traces: List[RelationshipTrace] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        matched_pattern_name: Optional[str] = None
        raw_triples: List[Tuple[str, str, str]] = []

        for pattern in ALL_PATTERNS:
            result = pattern.match(sentence)
            if result is not None:
                matched_pattern_name = pattern.name
                raw_triples = result
                break

        norm_pairs: List[Tuple[str, str]] = []
        edges_for_sentence: List[RelationshipEdge] = []

        for raw_src, rel, raw_tgt in raw_triples:
            norm_src = normalize_term(raw_src)
            norm_tgt = normalize_term(raw_tgt)
            norm_pairs.append((raw_src, norm_src))
            norm_pairs.append((raw_tgt, norm_tgt))

            if len(norm_src) < _MIN_TERM_LEN or len(norm_tgt) < _MIN_TERM_LEN:
                continue

            edge = RelationshipEdge(
                source_term=norm_src,
                relation_type=rel,
                target_term=norm_tgt,
                confidence=confidence,
                provenance=provenance,
            )
            edges_for_sentence.append(edge)

        all_edges.extend(edges_for_sentence)
        all_traces.append(RelationshipTrace(
            chunk_text=sentence,
            matched_pattern=matched_pattern_name,
            extracted_edges=[(e.source_term, e.relation_type, e.target_term) for e in edges_for_sentence],
            normalized_terms=norm_pairs,
        ))

    return RelationshipExtractionResult(
        edges=tuple(all_edges),
        traces=tuple(all_traces),
    )


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences on '. ' or trailing '.'"""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out
