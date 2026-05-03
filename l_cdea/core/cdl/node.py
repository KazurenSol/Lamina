from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from l_cdea.core.types.base import TypedValue
from .operator import CDLOperator


@dataclass
class CDLNode:
    """Single execution step in a CDL graph."""

    operator: CDLOperator
    inputs: List[CDLNode] = field(default_factory=list)
    value: Optional[TypedValue] = None

    def is_resolved(self) -> bool:
        return self.value is not None
