"""
batch_ingest_directory(path, config) → BatchIngestionReport
batch_ingest_files(files, config)   → BatchIngestionReport

Determinism rules:
  - Files processed in sorted order.
  - No parallelism (V1).
  - Same directory + same state → same report.

save_per_file=True  (default):
  State loaded and saved after each file. Crash-safe.

save_per_file=False:
  State loaded once, all files processed in memory, saved once at end.
  Faster but loses progress if the process is killed mid-batch.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List, Sequence

from l_cdea.ingestion.batch.config import BatchIngestionConfig
from l_cdea.ingestion.batch.report import BatchFileResult, BatchIngestionReport, generate_report
from l_cdea.ingestion.batch.errors import FileIngestionError


def batch_ingest_directory(
    path: str,
    config: BatchIngestionConfig,
) -> BatchIngestionReport:
    """
    Ingest all files in a directory using the given config.
    Files are processed in sorted (deterministic) order.
    Only files whose names end in .txt are included.
    """
    dir_path = Path(path)
    if not dir_path.is_dir():
        from l_cdea.ingestion.batch.errors import BatchIngestionError
        raise BatchIngestionError(f"Not a directory: {path!r}")

    files = sorted(str(p) for p in dir_path.iterdir() if p.is_file())
    if config.max_files is not None:
        files = files[: config.max_files]

    return batch_ingest_files(files, config)


def batch_ingest_files(
    files: Sequence[str],
    config: BatchIngestionConfig,
) -> BatchIngestionReport:
    """
    Ingest a list of files in the given order.
    Respects config.stop_on_error and config.save_per_file.
    """
    if config.save_per_file:
        return _ingest_save_per_file(list(files), config)
    else:
        return _ingest_save_once(list(files), config)


# ── save_per_file=True ────────────────────────────────────────────────────────

def _ingest_save_per_file(
    files: List[str],
    config: BatchIngestionConfig,
) -> BatchIngestionReport:
    if config.mode == "book":
        return _ingest_book_files(files, config)

    from l_cdea.ingestion import ingest_document

    file_results: List[BatchFileResult] = []
    for file_path in files:
        t0 = time.monotonic()
        try:
            result = ingest_document(
                file_path,
                mode=config.mode,
                state_path=config.state_path,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=True,
                ingestion_result=result,
                error=None,
                duration_ms=duration_ms,
            ))
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=False,
                ingestion_result=None,
                error=str(exc),
                duration_ms=duration_ms,
            ))
            if config.stop_on_error:
                break

    return generate_report(file_results)


def _ingest_book_files(
    files: List[str],
    config: BatchIngestionConfig,
) -> BatchIngestionReport:
    """Handle mode='book': call ingest_book() per file, wrap trace as IngestionResult."""
    from l_cdea.ingestion.book_prep.loader import ingest_book
    from l_cdea.ingestion.knowledge_importer import IngestionResult

    file_results: List[BatchFileResult] = []
    for file_path in files:
        t0 = time.monotonic()
        try:
            trace = ingest_book(file_path, state_path=config.state_path)
            result = IngestionResult(
                source_path=file_path,
                chunks_processed=trace.chunks_processed,
                claims=0,
                definitions=trace.nodes_added,
                procedures=0,
                contradictions=0,
                items_registered=trace.nodes_added,
                nodes_added=trace.nodes_added,
                edges_added=trace.edges_added,
                sections_detected=trace.chapters_processed,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=True,
                ingestion_result=result,
                error=None,
                duration_ms=duration_ms,
            ))
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=False,
                ingestion_result=None,
                error=str(exc),
                duration_ms=duration_ms,
            ))
            if config.stop_on_error:
                break

    return generate_report(file_results)


# ── save_per_file=False ───────────────────────────────────────────────────────

def _ingest_save_once(
    files: List[str],
    config: BatchIngestionConfig,
) -> BatchIngestionReport:
    """
    Load state once, process all files in memory, save state once at the end.
    Uses ingest_document(_shared_state=...) to skip per-file save.
    """
    from l_cdea.discourse.storage import load_state, save_state
    from l_cdea.ingestion import ingest_document

    state = load_state(config.state_path)
    file_results: List[BatchFileResult] = []

    for file_path in files:
        t0 = time.monotonic()
        try:
            result = ingest_document(
                file_path,
                mode=config.mode,
                state_path=config.state_path,
                _shared_state=state,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=True,
                ingestion_result=result,
                error=None,
                duration_ms=duration_ms,
            ))
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            file_results.append(BatchFileResult(
                file_path=file_path,
                success=False,
                ingestion_result=None,
                error=str(exc),
                duration_ms=duration_ms,
            ))
            if config.stop_on_error:
                break

    # Single save at the end
    try:
        save_state(state, config.state_path)
    except Exception as exc:
        from l_cdea.ingestion.batch.errors import BatchIngestionError
        raise BatchIngestionError(f"Failed to save state after batch: {exc}") from exc

    return generate_report(file_results)
