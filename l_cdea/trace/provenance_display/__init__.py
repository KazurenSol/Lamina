"""
l_cdea.trace.provenance_display — surface provenance in query output and trace logs.

Public API:
  DisplayedProvenance
  ProvenanceDisplayConfig / DEFAULT_CONFIG
  extract_provenance_from_node(node)
  extract_provenance_for_term(term, state)
  extract_provenance_from_lookup_traces(traces, value)
  extract_relationship_provenance(relationship_result)
  format_provenance_lines(entries, config)
  format_provenance_inline(entries, config)
  format_provenance_no_source()
  format_provenance_trace_section(term, entries, config)
"""
from l_cdea.trace.provenance_display.config import ProvenanceDisplayConfig, DEFAULT_CONFIG
from l_cdea.trace.provenance_display.extractor import (
    DisplayedProvenance,
    extract_provenance_from_node,
    extract_provenance_for_term,
    extract_provenance_from_lookup_traces,
    extract_relationship_provenance,
)
from l_cdea.trace.provenance_display.formatter import (
    format_provenance_lines,
    format_provenance_inline,
    format_provenance_no_source,
    format_provenance_trace_section,
)

__all__ = [
    "DisplayedProvenance",
    "ProvenanceDisplayConfig",
    "DEFAULT_CONFIG",
    "extract_provenance_from_node",
    "extract_provenance_for_term",
    "extract_provenance_from_lookup_traces",
    "extract_relationship_provenance",
    "format_provenance_lines",
    "format_provenance_inline",
    "format_provenance_no_source",
    "format_provenance_trace_section",
]
