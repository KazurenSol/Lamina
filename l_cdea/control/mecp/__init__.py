from dataclasses import dataclass
from typing import List

from l_cdea.normalization.canonicalizer import CanonicalizationResult
from .cost_model import MECPConfig, CostMap, compute_cost_map
from .scoring import GainMap, compute_gain_map
from .scheduler import ExecutionQueue, PriorityMap, schedule
from .pruning import ExecutionSubset, build_graph_sig_map, prune
from .exceptions import MECPError, CostModelError, SchedulingError, PruningError


@dataclass
class MECPResult:
    """
    Output contract of the MECP scheduler.
    Passed directly to the execution module.
    No graph was modified or executed — selection only.
    """
    execution_subset: ExecutionSubset
    execution_queue: ExecutionQueue
    cost_map: CostMap
    gain_map: GainMap
    priority_map: PriorityMap
    threshold_used: float


def run_mecp(
    canonical: CanonicalizationResult,
    config: MECPConfig = MECPConfig(),
) -> MECPResult:
    """
    MECP pipeline: cost → gain → schedule → prune.
    Deterministic. No CDL mutation. No DiscourseState access. No graph execution.
    """
    cost_map = compute_cost_map(canonical, config)
    gain_map = compute_gain_map(canonical)
    queue, priority_map = schedule(canonical, cost_map, gain_map)
    graph_to_sig = build_graph_sig_map(canonical.equivalence_map)
    subset = prune(queue, priority_map, graph_to_sig, config.threshold)

    return MECPResult(
        execution_subset=subset,
        execution_queue=queue,
        cost_map=cost_map,
        gain_map=gain_map,
        priority_map=priority_map,
        threshold_used=config.threshold,
    )


__all__ = [
    "run_mecp",
    "MECPResult",
    "MECPConfig",
    "CostMap",
    "GainMap",
    "ExecutionQueue",
    "ExecutionSubset",
    "MECPError",
    "CostModelError",
    "SchedulingError",
    "PruningError",
]
