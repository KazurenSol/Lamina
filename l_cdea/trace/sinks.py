"""
V1 trace sinks.

InMemoryTraceSink — stores records in a list; used by tests.
JSONLTraceSink    — appends one JSON line per record; deterministic serialization.
"""
from __future__ import annotations

import json
from typing import List

from l_cdea.trace.event import TraceSink, TraceRecord


class InMemoryTraceSink(TraceSink):
    """Accumulates TraceRecords in memory. Thread-unsafe; for testing only."""
    name = "memory"

    def __init__(self) -> None:
        self._records: List[TraceRecord] = []

    def write(self, record: TraceRecord) -> None:
        self._records.append(record)

    @property
    def records(self) -> List[TraceRecord]:
        return list(self._records)

    def latest(self) -> TraceRecord | None:
        return self._records[-1] if self._records else None

    def clear(self) -> None:
        self._records.clear()


class JSONLTraceSink(TraceSink):
    """
    Append-only JSONL sink. Each TraceRecord is serialized as one line.
    sort_keys=True ensures deterministic field ordering.
    """

    def __init__(self, path: str) -> None:
        self.name = f"jsonl:{path}"
        self._path = path

    def write(self, record: TraceRecord) -> None:
        from l_cdea.trace.formatter import to_dict
        line = json.dumps(to_dict(record), sort_keys=True, default=str)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
