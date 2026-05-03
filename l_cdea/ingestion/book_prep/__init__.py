"""Book ingestion preparation: parse, manifest, checkpoint, and resumable ingestion."""
from l_cdea.ingestion.book_prep.loader import ingest_book
from l_cdea.ingestion.book_prep.trace import BookIngestionTrace

__all__ = ["ingest_book", "BookIngestionTrace"]
