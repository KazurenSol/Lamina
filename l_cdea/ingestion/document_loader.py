"""
Load documents from disk into raw text with metadata.
Only plain text and JSON are supported in V1. No external parsers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RawDocument:
    content: str
    source_path: str
    title: str
    author: Optional[str] = None
    format: str = "text"


def load_document(path: str | Path) -> RawDocument:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        return RawDocument(
            content=json.dumps(data, indent=2),
            source_path=str(p),
            title=data.get("title", p.stem),
            author=data.get("author"),
            format="json",
        )

    content = p.read_text(encoding="utf-8")
    return RawDocument(
        content=content,
        source_path=str(p),
        title=p.stem,
        format="text",
    )
