from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from l_cdea.core.types.base import TypedValue
from l_cdea.core.cdl.operator import CDLOperator
from l_cdea.core.cdl.graph import CDLGraph
from l_cdea.core.router.intent import IntentFrame


@dataclass
class PlanningError:
    code: str
    message: str
    details: Dict = field(default_factory=dict)

    # Standard error codes
    OPERATOR_NOT_FOUND     = "OPERATOR_NOT_FOUND"
    OPERATOR_NOT_GOVERNED  = "OPERATOR_NOT_GOVERNED"   # strict mode: no governance record
    OPERATOR_NOT_ACTIVE    = "OPERATOR_NOT_ACTIVE"     # governed but candidate/deprecated
    SLOT_HYDRATION_FAILED  = "SLOT_HYDRATION_FAILED"
    TYPE_MISMATCH          = "TYPE_MISMATCH"
    DISCOURSE_LOOKUP_FAILED = "DISCOURSE_LOOKUP_FAILED"
    GRAPH_BUILD_FAILED     = "GRAPH_BUILD_FAILED"


@dataclass
class DiscourseLookupResult:
    hit: bool
    value: Optional[TypedValue]
    checked_keys: Tuple[str, ...]
    match_strategy: str


@dataclass
class QueryPlan:
    intent: IntentFrame
    cache_hit: bool

    # Cache hit path
    cached_result: Optional[TypedValue] = None
    cache_trace: Dict = field(default_factory=dict)

    # Cache miss path
    operator: Optional[CDLOperator] = None
    hydrated_slots: Dict[str, TypedValue] = field(default_factory=dict)
    graph: Optional[CDLGraph] = None

    # Always present
    provenance: Dict = field(default_factory=dict)
    errors: Tuple[PlanningError, ...] = field(default_factory=tuple)

    @property
    def is_executable(self) -> bool:
        return not self.cache_hit and self.graph is not None and not self.errors

    @property
    def is_fallback(self) -> bool:
        return self.intent.fallback


@dataclass
class PlanTrace:
    intent: IntentFrame
    discourse_lookup: Optional[DiscourseLookupResult]
    hydrated_slots: Dict[str, TypedValue]
    operator_key: str
    type_validation: Dict
    graph_nodes: int
    errors: List[PlanningError]
    # Ordering evidence: proves retype and graph_builder used the same source
    slot_order_used: Tuple[str, ...] = field(default_factory=tuple)
    retyped_slots: Dict[str, TypedValue] = field(default_factory=dict)
    operator_signature: Dict = field(default_factory=dict)
    # Governance trace: records which governed operator was resolved and how
    operator_governance_trace: Dict = field(default_factory=dict)
