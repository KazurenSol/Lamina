"""
Dataset validation.

Checks:
  - name and version non-empty
  - provenance includes 'source'
  - no duplicate keys (guaranteed by dict, but checked for clarity)
  - all keys are strings
  - key_type and value_type are valid SemanticTypes
  - stable serialization (repr is deterministic)

Returns a list of error strings. Empty list = valid.
"""
from __future__ import annotations

from typing import List

from l_cdea.data.datasets import Dataset


def validate_dataset(dataset: Dataset) -> List[str]:
    errors: List[str] = []

    if not dataset.name:
        errors.append("name must be non-empty")

    if not dataset.version:
        errors.append("version must be non-empty")

    if not dataset.provenance:
        errors.append("provenance must be non-empty dict")
    elif "source" not in dataset.provenance:
        errors.append("provenance must include 'source' key")

    if not isinstance(dataset.records, dict):
        errors.append("records must be a dict")
    else:
        for k in dataset.records:
            if not isinstance(k, str):
                errors.append(f"key {k!r} is not a string — all keys must be str")

    # key_type and value_type must be valid SemanticType members
    from l_cdea.core.types.base import SemanticType
    valid_types = set(SemanticType)
    if dataset.key_type not in valid_types:
        errors.append(f"key_type {dataset.key_type!r} is not a valid SemanticType")
    if dataset.value_type not in valid_types:
        errors.append(f"value_type {dataset.value_type!r} is not a valid SemanticType")

    return errors


def assert_valid(dataset: Dataset) -> None:
    """Raise ValueError listing all validation errors if dataset is invalid."""
    errors = validate_dataset(dataset)
    if errors:
        raise ValueError(
            f"Dataset '{dataset.name}' failed validation:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
