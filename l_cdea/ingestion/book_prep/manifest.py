"""
BookManifest: tracks ingestion progress for a single book.
Stored at <manifests_dir>/<book_id>.json

Rules:
- Atomic save: write to .tmp then os.replace (no partial writes).
- Deterministic JSON: sort_keys=True.
- Updated after each chapter completes.
- status: "in_progress" | "complete" | "failed"
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_MANIFESTS_DIR = ".l_cdea/manifests"


@dataclass
class BookManifest:
    book_id: str
    source_path: str
    chapters_total: int
    chapters_completed: int
    chunks_total: int
    chunks_processed: int
    nodes_added: int
    edges_added: int
    last_checkpoint: Optional[dict]
    status: str  # "in_progress" | "complete" | "failed"


def manifest_path(book_id: str, manifests_dir: str = DEFAULT_MANIFESTS_DIR) -> str:
    return os.path.join(manifests_dir, f"{book_id}.json")


def load_manifest(
    book_id: str,
    manifests_dir: str = DEFAULT_MANIFESTS_DIR,
) -> Optional[BookManifest]:
    path = manifest_path(book_id, manifests_dir)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BookManifest(
        book_id=data["book_id"],
        source_path=data["source_path"],
        chapters_total=data["chapters_total"],
        chapters_completed=data["chapters_completed"],
        chunks_total=data["chunks_total"],
        chunks_processed=data["chunks_processed"],
        nodes_added=data["nodes_added"],
        edges_added=data["edges_added"],
        last_checkpoint=data.get("last_checkpoint"),
        status=data["status"],
    )


def save_manifest(
    manifest: BookManifest,
    manifests_dir: str = DEFAULT_MANIFESTS_DIR,
) -> None:
    os.makedirs(manifests_dir, exist_ok=True)
    path = manifest_path(manifest.book_id, manifests_dir)
    tmp_path = path + ".tmp"
    data = {
        "book_id": manifest.book_id,
        "chapters_completed": manifest.chapters_completed,
        "chapters_total": manifest.chapters_total,
        "chunks_processed": manifest.chunks_processed,
        "chunks_total": manifest.chunks_total,
        "edges_added": manifest.edges_added,
        "last_checkpoint": manifest.last_checkpoint,
        "nodes_added": manifest.nodes_added,
        "source_path": manifest.source_path,
        "status": manifest.status,
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=2)
    os.replace(tmp_path, path)
