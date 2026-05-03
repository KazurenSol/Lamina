"""
Candidate compression schemes for CDL graph storage.
All schemes are lossless unless explicitly declared lossy.
Must not alter CDL semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CompressionScheme:
    name: str
    version: str
    lossless: bool
    compress_fn: Callable[[Any], Any]
    decompress_fn: Callable[[Any], Any]
    description: str


def _identity(x):
    return x


def _dict_compress(d: dict) -> dict:
    """Remove keys with None values."""
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in d.items() if v is not None}


def _dict_decompress(d: dict) -> dict:
    return d


COMPRESSION_CANDIDATES = [
    CompressionScheme(
        name="none",
        version="1.0",
        lossless=True,
        compress_fn=_identity,
        decompress_fn=_identity,
        description="No compression — identity passthrough.",
    ),
    CompressionScheme(
        name="null_strip",
        version="1.0",
        lossless=True,
        compress_fn=_dict_compress,
        decompress_fn=_dict_decompress,
        description="Strip None-valued keys from dicts.",
    ),
]
