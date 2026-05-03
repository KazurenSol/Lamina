"""
Provenance tracking for ingested knowledge items.
Every item that enters DiscourseState carries a KnowledgeItem wrapper.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class KnowledgeItem:
    content_graph: Any          # CDLGraph or symbolic value
    source_title: str
    source_path: str
    paragraph_index: int
    confidence: float = 1.0
    extraction_method: str = "direct"
    source_author: Optional[str] = None
    page: Optional[int] = None


_PROVENANCE_STORE: dict[str, KnowledgeItem] = {}


def register_item(key: str, item: KnowledgeItem) -> None:
    _PROVENANCE_STORE[key] = item


def get_provenance(key: str) -> Optional[KnowledgeItem]:
    return _PROVENANCE_STORE.get(key)


def all_sources() -> list[KnowledgeItem]:
    return list(_PROVENANCE_STORE.values())
