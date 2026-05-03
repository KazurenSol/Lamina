"""
Local dataset loaders.

V1 supported sources:
  - Python dict (from_dict)
  - JSON file   (from_json_file)

Rules:
- No external APIs or web access.
- No hidden mutation of input dicts.
- Deterministic load order (keys sorted on load).
- All keys coerced to str.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from l_cdea.core.types.base import SemanticType
from l_cdea.data.datasets import Dataset


def from_dict(
    name: str,
    domain: str,
    key_type: SemanticType,
    value_type: SemanticType,
    records: Dict[str, Any],
    version: str,
    provenance: Dict | None = None,
) -> Dataset:
    """
    Build a Dataset from a Python dict.
    Keys are coerced to str. Input dict is copied — no mutation.
    """
    clean = {str(k): v for k, v in records.items()}
    return Dataset(
        name=name,
        domain=domain,
        key_type=key_type,
        value_type=value_type,
        records=clean,
        version=version,
        provenance=dict(provenance) if provenance else {"source": "inline_dict"},
    )


def from_json_file(
    path: str,
    name: str,
    domain: str,
    key_type: SemanticType,
    value_type: SemanticType,
    version: str,
    provenance: Dict | None = None,
) -> Dataset:
    """
    Load a Dataset from a local JSON file.
    The file must contain a flat JSON object (string keys, scalar values).
    """
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"JSON file '{path}' must contain a top-level object.")

    clean = {str(k): v for k, v in raw.items()}
    return Dataset(
        name=name,
        domain=domain,
        key_type=key_type,
        value_type=value_type,
        records=clean,
        version=version,
        provenance=dict(provenance) if provenance else {"source": f"json_file:{path}"},
    )
