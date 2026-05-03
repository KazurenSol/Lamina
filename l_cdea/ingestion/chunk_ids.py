"""
Stable, deterministic chunk ID generation.

chunk_id = "chunk_" + sha256(source_path :: mode :: line_number :: normalized_text)[:8]

Rules:
  - Same inputs → same ID across runs (no uuid, no wall-clock time).
  - source_path included so IDs are scoped to their file.
  - line_number included so two identical lines in the same file get distinct IDs.
"""
from __future__ import annotations

import hashlib


def make_chunk_id(source_path: str, mode: str, line_number: int, text: str) -> str:
    content = f"{source_path}::{mode}::{line_number}::{text.strip().lower()}"
    return "chunk_" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
