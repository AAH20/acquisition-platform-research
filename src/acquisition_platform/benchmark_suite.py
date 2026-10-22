"""Benchmark suite with baseline persistence and regression gating.

The suite measures callable cases, compares them against stored baselines, and
reports regressions beyond a tolerance. It is the enforcement mechanism for
"exceed all benchmarks": a slower or less accurate run fails the gate instead
of silently shipping.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from acquisition_platform.exceptions import ValidationError


@dataclass(frozen=True)
class BenchmarkCase:
    """A single measured operation.

    Args:
        name: Unique case name.
        fn: Zero-argument callable to measure.
        target_ms: Maximum acceptable median duration in milliseconds.
    """

    name: str
    fn: Callable[[], Any]
    target_ms: float = 1000.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("BenchmarkCase name cannot be empty")
        if self.target_ms <= 0:
            raise ValidationError(f"Case '{self.name}' target_ms must be positive")


@dataclass(frozen=True)
class CaseResult:
    """Measured outcome for one case."""

    name: str
    value: float
    target: float
    passed: bool
    duration_ms: float
    unit: str = "ms"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "value": self.value,
            "target": self.target,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CaseResult":
        """Rebuild a result from its dictionary form."""
        return cls(
            name=str(payload["name"]),
            value=float(payload["value"]),
            target=float(payload["target"]),
            passed=bool(payload["passed"]),
            duration_ms=float(payload["duration_ms"]),
            unit=str(payload.get("unit", "ms")),
        )


@dataclass(frozen=True)
class Regression:
    """A case that got slower (or disappeared) relative to a baseline."""

    name: str
    baseline: float
    current: float
    change_pct: float
    regressed: bool
    missing: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "baseline": self.baseline,
            "current": self.current,
            "change_pct": self.change_pct,
            "regressed": self.regressed,
            "missing": self.missing,
        }


@dataclass
class SuiteReport:
    """Results of a benchmark suite run."""

    name: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Number of measured cases."""
        return len(self.results)

    @property
    def passed(self) -> int:
        """Number of cases inside their target."""
        return sum(1 for result in self.results if result.passed)

    @property
    def failed(self) -> int:
        """Number of cases outside their target."""
        return self.total - self.passed

    @property
    def score(self) -> float:
        """Fraction of cases passing, in [0, 1]."""
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "total": self.total,
            "passed": self.passed,
            "score": self.score,
            "results": [result.to_dict() for result in self.results],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SuiteReport":
        """Rebuild a report from its dictionary form."""
        return cls(
            name=str(payload["name"]),
            results=[CaseResult.from_dict(item) for item in payload.get("results", [])],
        )

    def save(self, path: str | Path) -> Path:
        """Persist the report as JSON."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "SuiteReport":
        """Load a report previously written by :meth:`save`."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(payload)

    def compare_to_baseline(
        self, baseline: "SuiteReport", tolerance: float = 0.10
    ) -> list[Regression]:
        """Compare durations against a baseline.

        Args:
            baseline: Reference report.
            tolerance: Fractional slowdown tolerated before flagging.

        Returns:
            Regressions beyond ``tolerance`` plus every case missing from this
            report.
        """
        if tolerance < 0:
            raise ValidationError("tolerance must be non-negative")
        baseline_by_name = {result.name: result for result in baseline.results}
        current_by_name = {result.name: result for result in self.results}
        regressions: list[Regression] = []

        for name, baseline_result in baseline_by_name.items():
            if name not in current_by_name:
                regressions.append(
                    Regression(
                        name=name,
                        baseline=baseline_result.value,
                        current=float("inf"),
                        change_pct=float("inf"),
                        regressed=True,
                        missing=True,
                    )
                )
                continue
            current = current_by_name[name]
            if baseline_result.value <= 0:
                change_pct = 0.0
            else:
                change_pct = (
                    (current.value - baseline_result.value) / baseline_result.value * 100.0
                )
            if change_pct > tolerance * 100.0:
                regressions.append(
                    Regression(
                        name=name,
                        baseline=baseline_result.value,
                        current=current.value,
                        change_pct=change_pct,
                        regressed=True,
                    )
                )
        return regressions


class BenchmarkSuite:
    """Collects cases and runs them with warmup and repetition."""

    def __init__(self, name: str) -> None:
        if not name:
            raise ValidationError("Suite name cannot be empty")
        self.name = name
        self._cases: list[BenchmarkCase] = []

    @property
    def cases(self) -> list[BenchmarkCase]:
        """Registered cases in insertion order."""
        return list(self._cases)

    def add(self, case: BenchmarkCase) -> None:
        """Register a case; names must be unique."""
        if any(existing.name == case.name for existing in self._cases):
            raise ValidationError(f"Duplicate benchmark case: '{case.name}'")
        self._cases.append(case)

    def run(self, repeats: int = 3, warmup: int = 1) -> SuiteReport:
        """Execute every case and return a report.

        Args:
            repeats: Timed runs per case; the median is reported.
            warmup: Untimed runs discarded before measuring.

        Returns:
            SuiteReport with one result per case.
        """
        if not self._cases:
            raise ValidationError("Cannot run a benchmark suite with no cases")
        if repeats < 1:
            raise ValidationError("repeats must be at least 1")
        if warmup < 0:
            raise ValidationError("warmup must be non-negative")

        results: list[CaseResult] = []
        for case in self._cases:
            for _ in range(warmup):
                case.fn()
            timings: list[float] = []
            for _ in range(repeats):
                started = time.perf_counter()
                case.fn()
                timings.append((time.perf_counter() - started) * 1000.0)
            median = statistics.median(timings)
            results.append(
                CaseResult(
                    name=case.name,
                    value=median,
                    target=case.target_ms,
                    passed=median <= case.target_ms,
                    duration_ms=median,
                )
            )
        return SuiteReport(name=self.name, results=results)
