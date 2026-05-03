"""
LOAD_DATA operator — structured data entry into the CDL system.
Source MUST be deterministic. Output is an ENTITY holding an ordered collection.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from l_cdea.core.types.base import SemanticType, TypedValue, TypeSignature
from l_cdea.core.cdl.operator import CDLOperator

# Default data directory — resolved relative to project root
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _load_data_transform(source: TypedValue) -> TypedValue:
    """
    Load data from a named source. Source is a string name resolved to a known data file.
    Deterministic: same source name → same output (no network, no randomness).
    """
    src = source.value
    if isinstance(src, dict):
        # Already a collection — pass through
        return TypedValue(value=src, type=SemanticType.ENTITY)
    if isinstance(src, str):
        path = _DATA_DIR / src
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TypedValue(value=data, type=SemanticType.ENTITY)
        # Source not found — return a labelled placeholder (deterministic)
        return TypedValue(value={"source": src, "status": "not_found"}, type=SemanticType.ENTITY)
    return TypedValue(value=str(src), type=SemanticType.ENTITY)


LOAD_DATA = CDLOperator(
    name="core.LOAD_DATA",
    signature=TypeSignature(
        input_types=(SemanticType.ENTITY,),
        output_type=SemanticType.ENTITY,
    ),
    transform=_load_data_transform,
)
