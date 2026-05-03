"""BatchIngestionConfig — controls batch ingestion behavior."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from l_cdea.ingestion.modes.config import VALID_MODES
from l_cdea.ingestion.knowledge_importer import DEFAULT_STATE_PATH
from l_cdea.ingestion.batch.errors import BatchIngestionError


@dataclass(frozen=True)
class BatchIngestionConfig:
    mode: str = "dictionary"
    state_path: str = DEFAULT_STATE_PATH
    stop_on_error: bool = False
    save_per_file: bool = True
    max_files: Optional[int] = None

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise BatchIngestionError(
                f"Invalid mode {self.mode!r}. Valid: {sorted(VALID_MODES)}"
            )
        if self.max_files is not None and self.max_files < 1:
            raise BatchIngestionError(
                f"max_files must be ≥ 1, got {self.max_files}"
            )
