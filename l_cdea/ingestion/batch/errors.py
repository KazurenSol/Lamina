"""Batch ingestion error types."""
from __future__ import annotations


class BatchIngestionError(Exception):
    """Raised when the entire batch cannot proceed (e.g. invalid config)."""


class FileIngestionError(Exception):
    """Wraps a per-file failure without aborting the batch."""

    def __init__(self, file_path: str, original: Exception) -> None:
        self.file_path = file_path
        self.original = original
        super().__init__(f"Failed to ingest {file_path!r}: {original}")
