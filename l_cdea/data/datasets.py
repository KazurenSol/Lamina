"""
Dataset and DatasetRecord — the atomic storage types for data-backed operators.

Rules:
- Immutable after construction.
- All keys are stored as strings for deterministic lookup.
- version is required and must be non-empty.
- provenance is required and must include at least 'source'.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from l_cdea.core.types.base import SemanticType


@dataclass(frozen=True)
class DatasetRecord:
    """A single key-value fact within a Dataset."""
    key: str
    value: Any
    provenance: Dict = field(default_factory=dict, compare=False)

    def __hash__(self):
        return hash((self.key, str(self.value)))


@dataclass
class Dataset:
    """
    A named, versioned, domain-scoped collection of typed key→value facts.

    key_type   : SemanticType of every key   (used for type validation)
    value_type : SemanticType of every value (must match operator output_type)
    records    : str → Any  (keys are always strings; values are Python scalars)
    """
    name: str
    domain: str
    key_type: SemanticType
    value_type: SemanticType
    records: Dict[str, Any]
    version: str
    provenance: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("Dataset.name must be non-empty")
        if not self.version:
            raise ValueError("Dataset.version must be non-empty")
        if not isinstance(self.records, dict):
            raise TypeError("Dataset.records must be a dict")

    def get(self, key: str) -> Any | None:
        """Exact-match lookup. Returns None on miss."""
        return self.records.get(key)

    def get_normalized(self, key: str) -> Any | None:
        """Case-insensitive, stripped lookup. Returns None on miss."""
        norm = key.strip().lower()
        for k, v in self.records.items():
            if k.strip().lower() == norm:
                return v
        return None

    def __len__(self) -> int:
        return len(self.records)

    def __contains__(self, key: str) -> bool:
        return key in self.records
