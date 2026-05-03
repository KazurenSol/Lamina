"""
Observability types for structured document ingestion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DocumentScalingTrace:
    total_sections: int
    total_chunks: int
    rejected_chunks: int
    sections: Tuple[Dict, ...]   # one dict per section with section_id/heading/level/chunk_count
