"""
Core types for structured document ingestion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class DocumentSection:
    section_id: str
    heading: Optional[str]
    level: int            # 0 = flat (no headings), 1 = #, 2 = ##, 3 = ###
    parent_id: Optional[str]
    text: str             # content belonging directly to this section (not children)
    start_line: int
    end_line: int


@dataclass(frozen=True)
class StructuredChunk:
    chunk_id: str
    section_id: str
    heading: Optional[str]
    text: str
    paragraph_index: int      # index within this section
    location: str             # "section:<section_id>:para:<paragraph_index>"


@dataclass(frozen=True)
class DocumentStructure:
    sections: Tuple[DocumentSection, ...]
