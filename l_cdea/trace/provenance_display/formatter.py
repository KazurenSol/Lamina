"""
format_provenance_lines(entries, config) → List[str]
format_provenance_inline(entries, config) → str   (for CLI output, indented)
format_provenance_no_source()            → str   (for fallback outputs)
"""
from __future__ import annotations

import os
from typing import List, Tuple

from l_cdea.trace.provenance_display.config import ProvenanceDisplayConfig, DEFAULT_CONFIG
from l_cdea.trace.provenance_display.extractor import DisplayedProvenance


def format_provenance_lines(
    entries: Tuple[DisplayedProvenance, ...],
    config: ProvenanceDisplayConfig = DEFAULT_CONFIG,
) -> List[str]:
    """
    Return one formatted line per provenance entry, up to config.max_entries.

    Format:
      [source: <file> | chunk: <id> | loc: <location> | conf: <conf>]
    """
    if not config.enabled:
        return []
    if not entries:
        return []

    lines = []
    for entry in entries[: config.max_entries]:
        parts = []

        # Source: prefer source_path filename, fall back to source_id
        source_label = None
        if entry.source_path:
            source_label = os.path.basename(entry.source_path)
        elif entry.source_id:
            source_label = entry.source_id
        if source_label:
            parts.append(f"source: {source_label}")

        if entry.chunk_id:
            parts.append(f"chunk: {entry.chunk_id}")

        if entry.location:
            parts.append(f"loc: {entry.location}")

        if config.show_confidence:
            parts.append(f"conf: {entry.confidence:.2f}")

        if config.show_trace_id and entry.trace_id:
            parts.append(f"trace: {entry.trace_id}")

        if parts:
            lines.append(f"  [{' | '.join(parts)}]")

    return lines


def format_provenance_inline(
    entries: Tuple[DisplayedProvenance, ...],
    config: ProvenanceDisplayConfig = DEFAULT_CONFIG,
) -> str:
    """Join formatted lines with newlines, ready for print()."""
    return "\n".join(format_provenance_lines(entries, config))


def format_provenance_no_source() -> str:
    return "  [no provenance]"


def format_provenance_trace_section(
    term: str,
    entries: Tuple[DisplayedProvenance, ...],
    config: ProvenanceDisplayConfig = DEFAULT_CONFIG,
) -> List[str]:
    """
    Structured lines for the [PROVENANCE] trace section.

    term: velocity
    entries:
      - source_path: physics_terms.txt
        chunk_id: chunk_9f82a1c3
        ...
    """
    if not config.enabled:
        return []

    lines = [f"  term: {term}", "  entries:"]
    if not entries:
        lines.append("    (none)")
        return lines

    for entry in entries[: config.max_entries]:
        lines.append(f"    - source_path:       {entry.source_path or '—'}")
        lines.append(f"      chunk_id:          {entry.chunk_id or '—'}")
        lines.append(f"      location:          {entry.location or '—'}")
        lines.append(f"      extraction_method: {entry.extraction_method}")
        if config.show_confidence:
            lines.append(f"      confidence:        {entry.confidence:.4f}")
        if config.show_trace_id:
            lines.append(f"      trace_id:          {entry.trace_id}")

    return lines
