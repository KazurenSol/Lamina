"""
Benchmark runner for adaptation candidates.
Reports timing and correctness; never auto-registers based on results.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, List


@dataclass
class BenchmarkResult:
    candidate_name: str
    iterations: int
    total_time_s: float
    avg_time_s: float
    passed_correctness: bool
    notes: str = ""


def run_benchmark(
    name: str,
    fn: Callable,
    args: tuple,
    expected: Any,
    iterations: int = 100,
) -> BenchmarkResult:
    start = time.perf_counter()
    result = None
    for _ in range(iterations):
        result = fn(*args)
    elapsed = time.perf_counter() - start

    passed = (result == expected)

    return BenchmarkResult(
        candidate_name=name,
        iterations=iterations,
        total_time_s=elapsed,
        avg_time_s=elapsed / iterations,
        passed_correctness=passed,
        notes="correctness verified" if passed else f"expected {expected!r}, got {result!r}",
    )


def run_all_benchmarks(candidates, test_cases: List[dict]) -> List[BenchmarkResult]:
    results = []
    for candidate in candidates:
        for case in test_cases:
            result = run_benchmark(
                name=candidate.name,
                fn=candidate.implementation,
                args=case["args"],
                expected=case["expected"],
                iterations=case.get("iterations", 50),
            )
            results.append(result)
    return results
