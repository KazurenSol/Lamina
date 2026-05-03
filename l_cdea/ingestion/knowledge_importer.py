"""
Full ingestion pipeline: Document → chunks → extraction → CDL → DiscourseState.
Follows hard rules: no CDL modification, provenance preserved, contradictions validated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from l_cdea.ingestion.document_loader import load_document
from l_cdea.ingestion.chunker import chunk_document_with_trace, DocumentChunk
from l_cdea.ingestion.claim_extractor import extract_claims, ExtractedClaim
from l_cdea.ingestion.definition_extractor import extract_definitions
from l_cdea.ingestion.procedure_extractor import extract_procedures
from l_cdea.ingestion.source_tracker import KnowledgeItem, register_item
from l_cdea.ingestion.contradiction_checker import check_contradictions
from l_cdea.ingestion.modes import validate_mode, get_mode_config, IngestionModeTrace
from l_cdea.ingestion.relationships.extractor import extract_relationships, RelationshipEdge

DEFAULT_STATE_PATH = ".l_cdea/discourse_state.json"


@dataclass
class IngestionResult:
    source_path: str
    chunks_processed: int
    claims: int
    definitions: int
    procedures: int
    contradictions: int
    items_registered: int
    nodes_added: int = 0
    edges_added: int = 0
    mode_trace: Optional[IngestionModeTrace] = None
    sections_detected: int = 0   # document_structured mode only


def ingest_document(
    path: str,
    existing_claims: List[ExtractedClaim] | None = None,
    state_path: Optional[str] = None,
    mode: str = "document",
    _shared_state=None,     # batch mode: pre-loaded state; if set, skip load+save
) -> IngestionResult:
    validate_mode(mode)
    mode_cfg = get_mode_config(mode)

    doc = load_document(path)

    if mode == "document_structured":
        return _ingest_structured(doc, path, existing_claims, state_path, _shared_state)

    chunks, rejected_count = chunk_document_with_trace(doc, mode=mode)

    mode_trace = IngestionModeTrace(
        mode=mode,
        min_chunk_chars=mode_cfg.min_chunk_chars,
        accepted_chunks=len(chunks),
        rejected_chunks=rejected_count,
    )

    all_claims = []
    all_definitions = []
    all_procedures = []
    all_relationships: List[RelationshipEdge] = []

    for chunk in chunks:
        all_claims.extend(extract_claims(chunk))
        all_definitions.extend(extract_definitions(chunk))
        all_procedures.extend(extract_procedures(chunk))
        all_relationships.extend(_extract_chunk_relationships(chunk, doc))

    contradictions = []
    if existing_claims:
        contradictions = check_contradictions(all_claims, existing_claims)

    items_registered = 0
    for i, claim in enumerate(all_claims):
        item = KnowledgeItem(
            content_graph=claim.text,
            source_title=claim.source_title,
            source_path=claim.source_path,
            paragraph_index=claim.paragraph_index,
            confidence=claim.confidence,
            extraction_method=claim.extraction_method,
        )
        register_item(f"{doc.title}::claim::{i}", item)
        items_registered += 1

    for i, defn in enumerate(all_definitions):
        item = KnowledgeItem(
            content_graph={"term": defn.term, "definition": defn.definition},
            source_title=defn.source_title,
            source_path=defn.source_path,
            paragraph_index=defn.paragraph_index,
            confidence=defn.confidence,
            extraction_method=defn.extraction_method,
        )
        register_item(f"{doc.title}::defn::{defn.term}", item)
        items_registered += 1

    if _shared_state is not None:
        nodes_added, edges_added = _add_definition_nodes(
            all_definitions, all_relationships, doc, _shared_state, mode=mode
        )
    else:
        nodes_added, edges_added = _persist_definitions(
            all_definitions, all_relationships, doc, state_path or DEFAULT_STATE_PATH, mode=mode
        )

    return IngestionResult(
        source_path=str(path),
        chunks_processed=len(chunks),
        claims=len(all_claims),
        definitions=len(all_definitions),
        procedures=len(all_procedures),
        contradictions=len(contradictions),
        items_registered=items_registered,
        nodes_added=nodes_added,
        edges_added=edges_added,
        mode_trace=mode_trace,
    )


def _ingest_structured(doc, path, existing_claims, state_path, _shared_state) -> IngestionResult:
    """
    Structured ingestion path: parse → section-aware chunking → extractors → state.
    StructuredChunks are converted to DocumentChunks carrying section_id / heading.
    """
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured
    from l_cdea.ingestion.document_scaling.trace import DocumentScalingTrace

    doc_structure = parse_document(doc.content)
    structured_chunks, rejected_count = chunk_structured(
        doc_structure, source_path=doc.source_path, source_title=doc.title
    )

    # Convert StructuredChunk → DocumentChunk, threading section context through
    chunks: List[DocumentChunk] = [
        DocumentChunk(
            text=sc.text,
            source_title=doc.title,
            source_path=doc.source_path,
            paragraph_index=sc.paragraph_index,
            chunk_id=sc.chunk_id,
            location=sc.location,
            section_id=sc.section_id,
            heading=sc.heading,
        )
        for sc in structured_chunks
    ]

    mode_trace = IngestionModeTrace(
        mode="document_structured",
        min_chunk_chars=40,
        accepted_chunks=len(chunks),
        rejected_chunks=rejected_count,
    )

    all_claims: List[ExtractedClaim] = []
    all_definitions = []
    all_procedures = []
    all_relationships: List[RelationshipEdge] = []

    for chunk in chunks:
        all_claims.extend(extract_claims(chunk))
        all_definitions.extend(extract_definitions(chunk))
        all_procedures.extend(extract_procedures(chunk))
        all_relationships.extend(_extract_chunk_relationships(chunk, doc))

    contradictions = []
    if existing_claims:
        contradictions = check_contradictions(all_claims, existing_claims)

    items_registered = 0
    for i, defn in enumerate(all_definitions):
        from l_cdea.ingestion.source_tracker import KnowledgeItem, register_item
        item = KnowledgeItem(
            content_graph={"term": defn.term, "definition": defn.definition},
            source_title=defn.source_title,
            source_path=defn.source_path,
            paragraph_index=defn.paragraph_index,
            confidence=defn.confidence,
            extraction_method=defn.extraction_method,
        )
        register_item(f"{doc.title}::defn::{defn.term}", item)
        items_registered += 1

    if _shared_state is not None:
        nodes_added, edges_added = _add_definition_nodes(
            all_definitions, all_relationships, doc, _shared_state, mode="document_structured"
        )
    else:
        nodes_added, edges_added = _persist_definitions(
            all_definitions, all_relationships, doc,
            state_path or DEFAULT_STATE_PATH, mode="document_structured"
        )

    return IngestionResult(
        source_path=str(path),
        chunks_processed=len(chunks),
        claims=len(all_claims),
        definitions=len(all_definitions),
        procedures=len(all_procedures),
        contradictions=len(contradictions),
        items_registered=items_registered,
        nodes_added=nodes_added,
        edges_added=edges_added,
        mode_trace=mode_trace,
        sections_detected=len(doc_structure.sections),
    )


def _extract_chunk_relationships(chunk, doc) -> List[RelationshipEdge]:
    """Build a Provenance for the chunk and extract relationship edges from its text."""
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    prov = Provenance(
        source_id=str(doc.title),
        source_type="document",
        extraction_method="relationship_extractor",
        confidence=0.75,
        trace_id=make_trace_id(str(doc.title), "relationship_extractor", chunk.paragraph_index),
        timestamp_index=chunk.paragraph_index,
        source_path=chunk.source_path,
        chunk_id=chunk.chunk_id,
        location=chunk.location,
    )
    result = extract_relationships(chunk.text, prov)
    return list(result.edges)


def _add_definition_nodes(
    all_definitions, all_relationships, doc, state, mode: str = "document"
) -> tuple:
    """
    Pure state mutation: create DiscourseNodes for definitions and DiscourseEdges
    for relationships. No I/O — caller is responsible for loading and saving state.
    Returns (nodes_added, edges_added).
    """
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.memory_graph import add_node
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.discourse.definition_retrieval.lookup import register_definition
    from l_cdea.discourse.definition_retrieval.normalization import normalize_term
    from l_cdea.core.types.base import SemanticType
    from l_cdea.ingestion.relationships.edge_builder import build_edges

    nodes_added = 0
    for defn in all_definitions:
        full_sentence = f"{defn.term} is {defn.definition}."
        norm_term = normalize_term(defn.term)
        node_id = make_node_id(SemanticType.ENTITY, full_sentence)

        if node_id not in state.nodes:
            prov = Provenance(
                source_id=str(doc.title),
                source_type="document",
                extraction_method=defn.extraction_method,
                confidence=defn.confidence,
                trace_id=make_trace_id(str(doc.title), defn.extraction_method, defn.paragraph_index),
                timestamp_index=defn.paragraph_index,
                source_path=defn.source_path,
                chunk_id=defn.chunk_id or f"{doc.title}::defn::{defn.term}",
                location=defn.location,
            )
            node = DiscourseNode(
                id=node_id,
                semantic_type=SemanticType.ENTITY,
                value=full_sentence,
                salience=1.0,
                created_at=defn.paragraph_index,
                updated_at=defn.paragraph_index,
                provenance=(prov,),
                metadata={
                    "category": "definition",
                    "term": norm_term,
                    "definition_text": full_sentence,
                    "ingestion_mode": mode,
                    "chunk_id": defn.chunk_id,
                    **({"section_id": defn.section_id} if defn.section_id else {}),
                    **({"heading": defn.heading} if defn.heading else {}),
                },
            )
            add_node(state, node)
            nodes_added += 1

        register_definition(
            defn.term,
            full_sentence,
            source_id=str(doc.title),
            confidence=defn.confidence,
            timestamp_index=defn.paragraph_index,
            node_id=node_id,
        )

    edges_added = build_edges(list(all_relationships), state)
    return nodes_added, edges_added


def _persist_definitions(
    all_definitions, all_relationships, doc, state_path: str, mode: str = "document"
) -> tuple:
    """Load state, add definition nodes and relationship edges, save state. Returns (nodes_added, edges_added)."""
    if not all_definitions and not all_relationships:
        return 0, 0
    from l_cdea.discourse.storage import load_state, save_state
    state = load_state(state_path)
    nodes_added, edges_added = _add_definition_nodes(
        all_definitions, all_relationships, doc, state, mode=mode
    )
    save_state(state, state_path)
    return nodes_added, edges_added
