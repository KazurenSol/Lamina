"""Batch ingestion result types and aggregation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from l_cdea.ingestion.knowledge_importer import IngestionResult


@dataclass(frozen=True)
class BatchFileResult:
    file_path: str
    success: bool
    ingestion_result: Optional[IngestionResult]
    error: Optional[str]
    duration_ms: int


@dataclass(frozen=True)
class BatchIngestionReport:
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    total_chunks: int
    total_definitions: int
    total_nodes_added: int
    total_contradictions: int
    file_results: Tuple[BatchFileResult, ...]
    total_sections_detected: int = 0          # document_structured mode only
    total_relationships_extracted: int = 0    # all modes

    def __str__(self) -> str:
        return (
            f"BatchIngestionReport("
            f"total_files={self.total_files}, "
            f"processed={self.processed_files}, "
            f"ok={self.successful_files}, "
            f"failed={self.failed_files}, "
            f"chunks={self.total_chunks}, "
            f"definitions={self.total_definitions}, "
            f"nodes_added={self.total_nodes_added}, "
            f"sections={self.total_sections_detected})"
        )


def generate_report(file_results: List[BatchFileResult]) -> BatchIngestionReport:
    """Aggregate per-file results into a BatchIngestionReport."""
    successful = [r for r in file_results if r.success]
    failed = [r for r in file_results if not r.success]

    total_chunks = sum(
        r.ingestion_result.chunks_processed
        for r in successful
        if r.ingestion_result is not None
    )
    total_definitions = sum(
        r.ingestion_result.definitions
        for r in successful
        if r.ingestion_result is not None
    )
    total_nodes_added = sum(
        r.ingestion_result.nodes_added
        for r in successful
        if r.ingestion_result is not None
    )
    total_contradictions = sum(
        r.ingestion_result.contradictions
        for r in successful
        if r.ingestion_result is not None
    )

    total_sections = sum(
        r.ingestion_result.sections_detected
        for r in successful
        if r.ingestion_result is not None
    )
    total_relationships = sum(
        r.ingestion_result.edges_added
        for r in successful
        if r.ingestion_result is not None
    )

    return BatchIngestionReport(
        total_files=len(file_results),
        processed_files=len(file_results),
        successful_files=len(successful),
        failed_files=len(failed),
        total_chunks=total_chunks,
        total_definitions=total_definitions,
        total_nodes_added=total_nodes_added,
        total_contradictions=total_contradictions,
        file_results=tuple(file_results),
        total_sections_detected=total_sections,
        total_relationships_extracted=total_relationships,
    )
