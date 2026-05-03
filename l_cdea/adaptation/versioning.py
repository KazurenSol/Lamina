"""
Version tracking for adaptation candidates and approved encodings.
Every adaptation must carry a semantic version string.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class AdaptationVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "AdaptationVersion") -> bool:
        return self.major == other.major


def parse_version(version_str: str) -> AdaptationVersion:
    parts = version_str.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version string: {version_str!r}")
    major, minor, patch = (int(p) for p in parts)
    return AdaptationVersion(major=major, minor=minor, patch=patch)


_VERSION_REGISTRY: Dict[str, AdaptationVersion] = {}


def register_version(name: str, version_str: str) -> AdaptationVersion:
    v = parse_version(version_str)
    _VERSION_REGISTRY[name] = v
    return v


def get_version(name: str) -> Optional[AdaptationVersion]:
    return _VERSION_REGISTRY.get(name)
