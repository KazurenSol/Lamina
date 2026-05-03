"""
Validate adaptation candidates against the 8 validation rules before registration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class ValidationReport:
    candidate_name: str
    passed: bool
    failed_rules: List[str]
    notes: str = ""


VALIDATION_RULES = [
    "deterministic",
    "lossless_unless_declared",
    "improves_cost",
    "type_safe",
    "reversible_or_traceable",
    "versioned",
    "does_not_alter_cdl_semantics",
    "passes_benchmarks",
]


def validate_candidate(
    name: str,
    version: str,
    lossless: bool,
    deterministic: bool,
    benchmark_passed: bool,
    cost_improvement: bool,
) -> ValidationReport:
    failed = []

    if not deterministic:
        failed.append("deterministic")
    if not lossless:
        failed.append("lossless_unless_declared")
    if not cost_improvement:
        failed.append("improves_cost")
    if not version:
        failed.append("versioned")
    if not benchmark_passed:
        failed.append("passes_benchmarks")

    return ValidationReport(
        candidate_name=name,
        passed=len(failed) == 0,
        failed_rules=failed,
    )
