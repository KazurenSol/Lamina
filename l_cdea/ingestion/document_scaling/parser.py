"""
parse_document(text) → DocumentStructure

Deterministic, rule-based document structure detection.

Heading detection rules (in priority order):
  1. Markdown: lines starting with "#", "##", "###" → level = count of "#" signs
  2. ALL CAPS: line with ≤ 10 words, all uppercase → level 1
  3. Short label: line ending with ":" and length ≤ 50 chars → level 2

Fallback: if no headings detected, the entire document is one section at level 0.

Tree construction: a stack of (level, section_id) tracks ancestry.
Each section's text is the content between its heading and the next heading.
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Optional, Tuple

from l_cdea.ingestion.document_scaling.section_model import (
    DocumentSection,
    DocumentStructure,
)

_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.*)")


def _make_section_id(level: int, heading: Optional[str], start_line: int) -> str:
    content = f"{level}::{heading or ''}::{start_line}"
    return "sec_" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def _detect_heading(line: str) -> Optional[Tuple[int, str]]:
    """Return (level, heading_text) if line is a heading, else None."""
    stripped = line.rstrip()
    if not stripped:
        return None

    # Rule 1: markdown headings
    m = _MARKDOWN_HEADING.match(stripped)
    if m:
        level = len(m.group(1))
        return level, m.group(2).strip()

    # Rule 2: ALL CAPS line ≤ 10 words
    words = stripped.split()
    if (len(words) <= 10
            and stripped == stripped.upper()
            and stripped.replace(" ", "").isalpha()):
        return 1, stripped.title()

    # Rule 3: short line ending with ":"
    if stripped.endswith(":") and len(stripped) <= 50:
        return 2, stripped[:-1].strip()

    return None


def parse_document(text: str) -> DocumentStructure:
    """
    Parse a document string into a DocumentStructure of sections.
    Preserves parent-child relationships for nested headings.
    Falls back to a single section if no headings are detected.
    """
    lines = text.splitlines()

    # Collect (line_index, level, heading) for all heading lines
    heading_positions: List[Tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        result = _detect_heading(line)
        if result is not None:
            level, heading_text = result
            heading_positions.append((i, level, heading_text))

    if not heading_positions:
        # Fallback: one section containing the entire document
        section = DocumentSection(
            section_id=_make_section_id(0, None, 0),
            heading=None,
            level=0,
            parent_id=None,
            text=text.strip(),
            start_line=0,
            end_line=len(lines) - 1,
        )
        return DocumentStructure(sections=(section,))

    # Build sections: each heading's text is lines[heading_line+1 : next_heading_line]
    sections: List[DocumentSection] = []
    stack: List[Tuple[int, str]] = []  # (level, section_id)

    for pos_idx, (line_i, level, heading) in enumerate(heading_positions):
        section_id = _make_section_id(level, heading, line_i)

        # Determine parent from stack: find deepest ancestor with level < this level
        parent_id: Optional[str] = None
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            parent_id = stack[-1][1]
        stack.append((level, section_id))

        # Section text: lines from after the heading line to before the next heading
        content_start = line_i + 1
        if pos_idx + 1 < len(heading_positions):
            content_end = heading_positions[pos_idx + 1][0]
        else:
            content_end = len(lines)

        section_lines = lines[content_start:content_end]
        section_text = "\n".join(section_lines).strip()

        sections.append(DocumentSection(
            section_id=section_id,
            heading=heading,
            level=level,
            parent_id=parent_id,
            text=section_text,
            start_line=line_i,
            end_line=content_end - 1,
        ))

    return DocumentStructure(sections=tuple(sections))
