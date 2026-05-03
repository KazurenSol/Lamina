"""
DatasetRegistry — module-level singleton for registered datasets.

Rules:
- Duplicate name+version pair is rejected with DatasetConflictError.
- Same name, different version: allowed (new entry under name:version key).
- Lookup by name always returns the most recently registered version.
- Registration order is deterministic (insertion order preserved).
- No network access.
"""
from __future__ import annotations

from typing import Dict, List

from l_cdea.data.datasets import Dataset


class DatasetConflictError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class _Registry:
    def __init__(self) -> None:
        # Primary store: name → Dataset (latest registered wins for name lookup)
        self._by_name: Dict[str, Dataset] = {}
        # Versioned store: "name:version" → Dataset (immutable)
        self._by_version: Dict[str, Dataset] = {}

    def register(self, dataset: Dataset) -> None:
        version_key = f"{dataset.name}:{dataset.version}"
        if version_key in self._by_version:
            existing = self._by_version[version_key]
            if existing.records == dataset.records:
                return  # exact duplicate — idempotent
            raise DatasetConflictError(
                f"Dataset '{version_key}' already registered with different content."
            )
        self._by_version[version_key] = dataset
        self._by_name[dataset.name] = dataset  # latest version wins

    def get(self, name: str) -> Dataset:
        if name not in self._by_name:
            raise DatasetNotFoundError(f"Dataset '{name}' not found in registry.")
        return self._by_name[name]

    def list(self) -> List[str]:
        return sorted(self._by_name.keys())

    def has(self, name: str) -> bool:
        return name in self._by_name

    def clear(self) -> None:
        self._by_name.clear()
        self._by_version.clear()


DatasetRegistry = _Registry()


def register_dataset(dataset: Dataset) -> None:
    DatasetRegistry.register(dataset)


def get_dataset(name: str) -> Dataset:
    return DatasetRegistry.get(name)


def list_datasets() -> List[str]:
    return DatasetRegistry.list()


def has_dataset(name: str) -> bool:
    return DatasetRegistry.has(name)
