"""
l_cdea.ingestion.batch — deterministic batch ingestion of dictionary files.

Public API:
  batch_ingest_directory(path, config) → BatchIngestionReport
  batch_ingest_files(files, config)    → BatchIngestionReport
  BatchIngestionConfig
  BatchIngestionReport
  BatchFileResult
  BatchIngestionError
  FileIngestionError
"""
from l_cdea.ingestion.batch.config import BatchIngestionConfig
from l_cdea.ingestion.batch.report import BatchFileResult, BatchIngestionReport, generate_report
from l_cdea.ingestion.batch.errors import BatchIngestionError, FileIngestionError
from l_cdea.ingestion.batch.batch import batch_ingest_directory, batch_ingest_files

__all__ = [
    "BatchIngestionConfig",
    "BatchFileResult",
    "BatchIngestionReport",
    "generate_report",
    "BatchIngestionError",
    "FileIngestionError",
    "batch_ingest_directory",
    "batch_ingest_files",
]
