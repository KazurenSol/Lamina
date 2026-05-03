"""
ingest_book(path, resume=True, ...) → BookIngestionTrace

Full book ingestion pipeline:
  1. Parse book → BookStructure (chapters + section IDs)
  2. Load or create manifest
  3. For each pending chapter:
       - detect glossary_line_mode or paragraph_mode
       - chunk accordingly → extract → persist → checkpoint
  4. Mark manifest complete

Per-chapter mode switching:
  glossary_line_mode — line-based chunking for definition-dense chapters
  paragraph_mode     — structured document chunking (default)

Resume rules:
  - manifest exists and status != "failed/complete" and resume=True → skip completed chapters.
  - status == "failed" → start fresh regardless of resume flag.
  - Re-running on complete book is idempotent (no duplicate nodes/edges).

Every node carries: book_id, chapter_id, chunk_mode, section_id/heading (paragraph),
line_index (glossary), paragraph_index, in its metadata dict.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

from l_cdea.ingestion.book_prep.book_model import BookChapter, BookStructure
from l_cdea.ingestion.book_prep.checkpoint import Checkpoint, checkpoint_to_dict
from l_cdea.ingestion.book_prep.glossary_detector import GlossaryDetectionResult, detect_glossary_mode
from l_cdea.ingestion.book_prep.manifest import (
    DEFAULT_MANIFESTS_DIR,
    BookManifest,
    load_manifest,
    save_manifest,
)
from l_cdea.ingestion.book_prep.parser import parse_book
from l_cdea.ingestion.book_prep.trace import BookIngestionTrace, GlossaryModeTrace
from l_cdea.ingestion.knowledge_importer import DEFAULT_STATE_PATH


def ingest_book(
    path: str,
    resume: bool = True,
    state_path: Optional[str] = None,
    max_chapters: Optional[int] = None,
    manifests_dir: str = DEFAULT_MANIFESTS_DIR,
) -> BookIngestionTrace:
    """
    Ingest a book file into the DiscourseState.
    Returns a BookIngestionTrace with counts, resume flag, and per-chapter mode info.
    """
    effective_state_path = state_path or DEFAULT_STATE_PATH

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    file_size = os.path.getsize(path)
    source_path = os.path.abspath(path)

    book_structure = parse_book(text, source_path, file_size)
    book_id = book_structure.metadata.book_id
    lines = text.splitlines()

    existing_manifest = load_manifest(book_id, manifests_dir)
    resumed = False
    start_idx = 0

    if (resume
            and existing_manifest is not None
            and existing_manifest.status != "failed"
            and existing_manifest.status != "complete"):
        start_idx = existing_manifest.chapters_completed
        manifest = BookManifest(
            book_id=existing_manifest.book_id,
            source_path=existing_manifest.source_path,
            chapters_total=existing_manifest.chapters_total,
            chapters_completed=existing_manifest.chapters_completed,
            chunks_total=existing_manifest.chunks_total,
            chunks_processed=existing_manifest.chunks_processed,
            nodes_added=existing_manifest.nodes_added,
            edges_added=existing_manifest.edges_added,
            last_checkpoint=existing_manifest.last_checkpoint,
            status="in_progress",
        )
        resumed = True
    else:
        manifest = BookManifest(
            book_id=book_id,
            source_path=source_path,
            chapters_total=len(book_structure.chapters),
            chapters_completed=0,
            chunks_total=0,
            chunks_processed=0,
            nodes_added=0,
            edges_added=0,
            last_checkpoint=None,
            status="in_progress",
        )

    chapters_to_process = list(book_structure.chapters)[start_idx:]
    if max_chapters is not None:
        chapters_to_process = chapters_to_process[:max_chapters]

    chapters_processed = 0
    total_chunks = manifest.chunks_processed
    total_nodes = manifest.nodes_added
    total_edges = manifest.edges_added
    chapter_mode_traces: List[GlossaryModeTrace] = []

    try:
        for chapter in chapters_to_process:
            chapter_text = _extract_chapter_text(lines, chapter)
            chunks_done, nodes_done, edges_done, gloss_result = _ingest_chapter(
                chapter, chapter_text, book_structure, effective_state_path
            )
            total_chunks += chunks_done
            total_nodes += nodes_done
            total_edges += edges_done
            chapters_processed += 1

            chapter_mode_traces.append(GlossaryModeTrace(
                chapter_id=chapter.chapter_id,
                glossary_mode=gloss_result.glossary_mode,
                total_lines=gloss_result.total_lines,
                valid_lines=gloss_result.valid_lines,
                ratio=gloss_result.ratio,
            ))

            cp = Checkpoint(
                book_id=book_id,
                chapter_id=chapter.chapter_id,
                chunk_index=total_chunks,
                timestamp=start_idx + chapters_processed,
            )
            manifest = BookManifest(
                book_id=manifest.book_id,
                source_path=manifest.source_path,
                chapters_total=manifest.chapters_total,
                chapters_completed=start_idx + chapters_processed,
                chunks_total=manifest.chunks_total,
                chunks_processed=total_chunks,
                nodes_added=total_nodes,
                edges_added=total_edges,
                last_checkpoint=checkpoint_to_dict(cp),
                status="in_progress",
            )
            save_manifest(manifest, manifests_dir)

        all_done = manifest.chapters_completed >= len(book_structure.chapters)
        manifest = BookManifest(
            book_id=manifest.book_id,
            source_path=manifest.source_path,
            chapters_total=manifest.chapters_total,
            chapters_completed=manifest.chapters_completed,
            chunks_total=manifest.chunks_total,
            chunks_processed=manifest.chunks_processed,
            nodes_added=manifest.nodes_added,
            edges_added=manifest.edges_added,
            last_checkpoint=manifest.last_checkpoint,
            status="complete" if all_done else "in_progress",
        )
        save_manifest(manifest, manifests_dir)

    except Exception:
        failed_manifest = BookManifest(
            book_id=manifest.book_id,
            source_path=manifest.source_path,
            chapters_total=manifest.chapters_total,
            chapters_completed=manifest.chapters_completed,
            chunks_total=manifest.chunks_total,
            chunks_processed=manifest.chunks_processed,
            nodes_added=manifest.nodes_added,
            edges_added=manifest.edges_added,
            last_checkpoint=manifest.last_checkpoint,
            status="failed",
        )
        save_manifest(failed_manifest, manifests_dir)
        raise

    return BookIngestionTrace(
        book_id=book_id,
        chapters_total=len(book_structure.chapters),
        chapters_processed=chapters_processed,
        chunks_processed=total_chunks,
        nodes_added=total_nodes,
        edges_added=total_edges,
        resumed=resumed,
        chapter_modes=tuple(chapter_mode_traces),
    )


def _extract_chapter_text(lines: List[str], chapter: BookChapter) -> str:
    """Extract body text of a chapter (lines after the heading line)."""
    content_start = chapter.start_line + 1
    content_end = chapter.end_line + 1
    return "\n".join(lines[content_start:content_end]).strip()


def _ingest_chapter(
    chapter: BookChapter,
    chapter_text: str,
    book_structure: BookStructure,
    state_path: str,
) -> Tuple[int, int, int, GlossaryDetectionResult]:
    """
    Detect mode, chunk, extract, and persist one chapter.
    Returns (chunks_processed, nodes_added, edges_added, glossary_detection_result).
    """
    from l_cdea.ingestion.definition_extractor import extract_definitions
    from l_cdea.ingestion.relationships.extractor import extract_relationships
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.discourse.storage import load_state, save_state

    book_id = book_structure.metadata.book_id
    source_path = book_structure.metadata.source_path
    source_title = book_structure.metadata.title or os.path.basename(source_path)

    gloss_result = detect_glossary_mode(chapter_text)

    if gloss_result.glossary_mode:
        chunks = _glossary_chunks(chapter_text, chapter, source_path, source_title)
    else:
        chunks = _paragraph_chunks(chapter_text, source_path, source_title)

    all_definitions = []
    all_relationships = []

    for chunk in chunks:
        all_definitions.extend(extract_definitions(chunk))
        prov = Provenance(
            source_id=source_title,
            source_type="document",
            extraction_method="relationship_extractor",
            confidence=0.75,
            trace_id=make_trace_id(source_title, "relationship_extractor", chunk.paragraph_index),
            timestamp_index=chunk.paragraph_index,
            source_path=chunk.source_path,
            chunk_id=chunk.chunk_id,
            location=chunk.location,
        )
        result = extract_relationships(chunk.text, prov)
        all_relationships.extend(result.edges)

    chunk_mode = "glossary_line" if gloss_result.glossary_mode else "paragraph"
    state = load_state(state_path)
    nodes_added, edges_added = _add_book_nodes(
        all_definitions,
        list(all_relationships),
        book_id,
        chapter.chapter_id,
        chunk_mode,
        source_title,
        source_path,
        state,
    )
    save_state(state, state_path)

    return len(chunks), nodes_added, edges_added, gloss_result


def _glossary_chunks(
    chapter_text: str,
    chapter: BookChapter,
    source_path: str,
    source_title: str,
) -> list:
    """Line-based chunking for glossary-style chapters."""
    from l_cdea.ingestion.chunker import DocumentChunk
    from l_cdea.ingestion.modes.filter import is_valid_dictionary_chunk
    from l_cdea.ingestion.chunk_ids import make_chunk_id

    chunks = []
    for line_idx, raw_line in enumerate(chapter_text.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        if not is_valid_dictionary_chunk(line):
            continue
        location = f"chapter:{chapter.chapter_id}:line:{line_idx}"
        chunk_id = make_chunk_id(source_path, "book_glossary", line_idx, line)
        chunks.append(DocumentChunk(
            text=line,
            source_title=source_title,
            source_path=source_path,
            paragraph_index=line_idx,
            chunk_id=chunk_id,
            location=location,
            section_id=None,
            heading=None,
        ))
    return chunks


def _paragraph_chunks(
    chapter_text: str,
    source_path: str,
    source_title: str,
) -> list:
    """Paragraph-based chunking via document_scaling (unchanged path)."""
    from l_cdea.ingestion.chunker import DocumentChunk
    from l_cdea.ingestion.document_scaling.parser import parse_document
    from l_cdea.ingestion.document_scaling.chunker import chunk_structured

    doc_structure = parse_document(chapter_text)
    structured_chunks, _ = chunk_structured(
        doc_structure,
        source_path=source_path,
        source_title=source_title,
    )
    return [
        DocumentChunk(
            text=sc.text,
            source_title=source_title,
            source_path=source_path,
            paragraph_index=sc.paragraph_index,
            chunk_id=sc.chunk_id,
            location=sc.location,
            section_id=sc.section_id,
            heading=sc.heading,
        )
        for sc in structured_chunks
    ]


def _add_book_nodes(
    all_definitions,
    all_relationships,
    book_id: str,
    chapter_id: str,
    chunk_mode: str,
    source_title: str,
    source_path: str,
    state,
) -> Tuple[int, int]:
    """
    Add definition nodes and relationship edges to state with full book metadata.
    Skips nodes that already exist (idempotent). Returns (nodes_added, edges_added).
    """
    from l_cdea.core.types.base import SemanticType
    from l_cdea.discourse.node import DiscourseNode, make_node_id
    from l_cdea.discourse.memory_graph import add_node
    from l_cdea.discourse.provenance.model import Provenance, make_trace_id
    from l_cdea.discourse.definition_retrieval.lookup import register_definition
    from l_cdea.discourse.definition_retrieval.normalization import normalize_term
    from l_cdea.ingestion.relationships.edge_builder import build_edges

    nodes_added = 0
    for defn in all_definitions:
        full_sentence = f"{defn.term} is {defn.definition}."
        norm_term = normalize_term(defn.term)
        node_id = make_node_id(SemanticType.ENTITY, full_sentence)

        if node_id not in state.nodes:
            prov = Provenance(
                source_id=source_title,
                source_type="document",
                extraction_method=defn.extraction_method,
                confidence=defn.confidence,
                trace_id=make_trace_id(source_title, defn.extraction_method, defn.paragraph_index),
                timestamp_index=defn.paragraph_index,
                source_path=source_path,
                chunk_id=defn.chunk_id or f"{source_title}::defn::{defn.term}",
                location=defn.location,
            )
            metadata = {
                "category": "definition",
                "term": norm_term,
                "definition_text": full_sentence,
                "ingestion_mode": "book",
                "chunk_mode": chunk_mode,
                "chunk_id": defn.chunk_id,
                "book_id": book_id,
                "chapter_id": chapter_id,
                "paragraph_index": defn.paragraph_index,
            }
            if chunk_mode == "glossary_line":
                # Extract line_index from location "chapter:<id>:line:<n>"
                loc = defn.location or ""
                if ":line:" in loc:
                    try:
                        metadata["line_index"] = int(loc.split(":line:")[-1])
                    except ValueError:
                        pass
            else:
                if defn.section_id:
                    metadata["section_id"] = defn.section_id
                if defn.heading:
                    metadata["heading"] = defn.heading

            node = DiscourseNode(
                id=node_id,
                semantic_type=SemanticType.ENTITY,
                value=full_sentence,
                salience=1.0,
                created_at=defn.paragraph_index,
                updated_at=defn.paragraph_index,
                provenance=(prov,),
                metadata=metadata,
            )
            add_node(state, node)
            nodes_added += 1

        register_definition(
            defn.term,
            full_sentence,
            source_id=source_title,
            confidence=defn.confidence,
            timestamp_index=defn.paragraph_index,
            node_id=node_id,
        )

    edges_added = build_edges(list(all_relationships), state)
    return nodes_added, edges_added
