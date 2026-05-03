"""
parse_book(text, source_path, file_size) → BookStructure

Chapter detection rules (in priority order):
  1. "Chapter X" / "CHAPTER X" / "Chapter X: Title" plain-text patterns
  2. Markdown "# Chapter X" headings
  3. ALL CAPS short lines (1–5 words, letters only) — book-style chapter headers

Fallback: entire document = single chapter at index 0.

book_id = sha256(source_path + file_size + first_1k_chars)[:16]
chapter_id = "chap_" + sha256(book_id + index + title)[:12]
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Optional, Tuple

from l_cdea.ingestion.book_prep.book_model import BookChapter, BookMetadata, BookStructure

_CHAPTER_PLAIN = re.compile(
    r"^(Chapter|CHAPTER)\s+\S+(\s*[:.\-]\s*.*)?$"
)
_CHAPTER_MARKDOWN = re.compile(
    r"^#{1,3}\s+(Chapter|CHAPTER)\s+",
    re.IGNORECASE,
)


def _make_book_id(source_path: str, file_size: int, first_1k: str) -> str:
    content = f"{source_path}::{file_size}::{first_1k}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _make_chapter_id(book_id: str, index: int, title: Optional[str]) -> str:
    content = f"{book_id}::chapter::{index}::{title or ''}"
    return "chap_" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def _is_chapter_heading(line: str) -> Optional[str]:
    """Return chapter title string if line is a chapter heading, else None."""
    stripped = line.rstrip()
    if not stripped:
        return None

    # "Chapter X" / "CHAPTER X" / "Chapter X: Title"
    if _CHAPTER_PLAIN.match(stripped):
        return stripped

    # "# Chapter X" markdown
    m = _CHAPTER_MARKDOWN.match(stripped)
    if m:
        return re.sub(r"^#{1,3}\s+", "", stripped).strip()

    # ALL CAPS short line (1–5 words, letters only) — e.g. "INTRODUCTION"
    words = stripped.split()
    if (1 <= len(words) <= 5
            and stripped == stripped.upper()
            and stripped.replace(" ", "").isalpha()):
        return stripped.title()

    return None


def _section_ids_for_text(chapter_text: str) -> Tuple[str, ...]:
    """Parse chapter text through document_scaling and return all section_ids."""
    from l_cdea.ingestion.document_scaling.parser import parse_document
    doc_structure = parse_document(chapter_text)
    return tuple(s.section_id for s in doc_structure.sections)


def parse_book(
    text: str,
    source_path: str = "",
    file_size: int = 0,
) -> BookStructure:
    lines = text.splitlines()
    total_lines = len(lines)
    first_1k = text[:1000]
    book_id = _make_book_id(source_path, file_size, first_1k)

    # Collect (line_index, title) for all chapter headings
    chapter_positions: List[Tuple[int, str]] = []
    for i, line in enumerate(lines):
        title = _is_chapter_heading(line)
        if title is not None:
            chapter_positions.append((i, title))

    if not chapter_positions:
        # Fallback: single chapter spanning the whole document
        chapter_id = _make_chapter_id(book_id, 0, None)
        section_ids = _section_ids_for_text(text.strip())
        chapter = BookChapter(
            chapter_id=chapter_id,
            title=None,
            start_line=0,
            end_line=total_lines - 1,
            section_ids=section_ids,
        )
        metadata = BookMetadata(
            book_id=book_id,
            title=None,
            author=None,
            source_path=source_path,
            total_lines=total_lines,
        )
        return BookStructure(metadata=metadata, chapters=(chapter,))

    chapters = []
    for idx, (line_i, title) in enumerate(chapter_positions):
        chapter_id = _make_chapter_id(book_id, idx, title)
        content_start = line_i + 1
        content_end = chapter_positions[idx + 1][0] if idx + 1 < len(chapter_positions) else total_lines
        chapter_text = "\n".join(lines[content_start:content_end]).strip()
        section_ids = _section_ids_for_text(chapter_text)
        chapters.append(BookChapter(
            chapter_id=chapter_id,
            title=title,
            start_line=line_i,
            end_line=content_end - 1,
            section_ids=section_ids,
        ))

    metadata = BookMetadata(
        book_id=book_id,
        title=None,
        author=None,
        source_path=source_path,
        total_lines=total_lines,
    )
    return BookStructure(metadata=metadata, chapters=tuple(chapters))
