"""Tests for the benchmark suite and regression gate."""

from __future__ import annotations

import time

import pytest

from acquisition_platform.benchmark_suite import (
    BenchmarkCase,
    BenchmarkSuite,
    CaseResult,
    Regression,
    SuiteReport,
)
from acquisition_platform.exceptions import ValidationError


def fast() -> int:
    return sum(range(10))


def slower() -> int:
    time.sleep(0.001)
    return sum(range(10))


class TestBenchmarkSuite:
    def test_run_collects_results(self):
        suite = BenchmarkSuite("core")
        suite.add(BenchmarkCase("fast", fast, target_ms=100.0))
        report = suite.run(repeats=2, warmup=0)
        assert len(report.results) == 1
        assert report.results[0].name == "fast"
        assert report.results[0].value > 0

    def test_passed_count_and_score(self):
        suite = BenchmarkSuite("core")
        suite.add(BenchmarkCase("fast", fast, target_ms=100.0))
        suite.add(BenchmarkCase("slow", slower, target_ms=0.0001))
        report = suite.run(repeats=2, warmup=0)
        assert report.total == 2
        assert report.passed == 1
        assert report.score == pytest.approx(0.5)

    def test_duplicate_case_names_rejected(self):
        suite = BenchmarkSuite("core")
        suite.add(BenchmarkCase("fast", fast, target_ms=100.0))
        with pytest.raises(ValidationError):
            suite.add(BenchmarkCase("fast", fast, target_ms=100.0))

    def test_empty_suite_raises(self):
        with pytest.raises(ValidationError):
            BenchmarkSuite("empty").run()

    def test_report_roundtrip(self):
        suite = BenchmarkSuite("core")
        suite.add(BenchmarkCase("fast", fast, target_ms=100.0))
        report = suite.run(repeats=1, warmup=0)
        restored = SuiteReport.from_dict(report.to_dict())
        assert restored.name == report.name
        assert restored.results[0].name == "fast"
        assert restored.results[0].value == pytest.approx(report.results[0].value)


class TestRegressionGate:
    def _report(self, value: float) -> SuiteReport:
        return SuiteReport(
            name="core",
            results=[
                CaseResult(
                    name="op",
                    value=value,
                    target=10.0,
                    passed=True,
                    duration_ms=value,
                    unit="ms",
                )
            ],
        )

    def test_no_regression_when_faster(self):
        baseline = self._report(10.0)
        current = self._report(9.0)
        regressions = current.compare_to_baseline(baseline, tolerance=0.1)
        assert regressions == []

    def test_regression_detected_beyond_tolerance(self):
        baseline = self._report(10.0)
        current = self._report(13.0)
        regressions = current.compare_to_baseline(baseline, tolerance=0.1)
        assert len(regressions) == 1
        assert regressions[0].regressed is True
        assert regressions[0].change_pct == pytest.approx(30.0)

    def test_regression_inside_tolerance_ignored(self):
        baseline = self._report(10.0)
        current = self._report(10.5)
        assert current.compare_to_baseline(baseline, tolerance=0.1) == []

    def test_regression_serialises(self):
        regression = Regression(
            name="op", baseline=10.0, current=13.0, change_pct=30.0, regressed=True
        )
        assert regression.to_dict()["change_pct"] == 30.0

    def test_missing_case_is_reported(self):
        baseline = self._report(10.0)
        current = SuiteReport(name="core", results=[])
        regressions = current.compare_to_baseline(baseline, tolerance=0.1)
        assert len(regressions) == 1
        assert regressions[0].regressed is True

    def test_noise_floor_suppresses_microbenchmark_jitter(self):
        baseline = self._report(3.7)
        current = self._report(5.0)  # +35% but only 1.3 ms
        regressions = current.compare_to_baseline(
            baseline, tolerance=0.25, noise_floor_ms=2.0
        )
        assert regressions == []

    def test_noise_floor_does_not_mask_real_regression(self):
        baseline = self._report(3.7)
        current = self._report(6.2)  # +68% and +2.5 ms
        regressions = current.compare_to_baseline(
            baseline, tolerance=0.25, noise_floor_ms=2.0
        )
        assert len(regressions) == 1
        assert regressions[0].regressed is True
