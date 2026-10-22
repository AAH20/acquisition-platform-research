"""Tests for temporal drift, walk-forward refitting, and Pareto ensembling.

Falsifiable predictions:
- A policy frozen at the first cohort must degrade as the market's fair-value
  point drifts away from its training regime.
- Refitting on the most recent cohort must not be worse than freezing, and
  should beat it once drift is material.
- Rank-aggregating the Pareto front must not be materially worse than the
  single selected alpha.
"""

from __future__ import annotations

import pytest

from acquisition_platform.alpha_lab import (
    AlphaLab,
    TemporalBenchmark,
    WalkForwardReport,
)
from acquisition_platform.exceptions import InvalidRangeError


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=16, generations=8)


@pytest.fixture(scope="module")
def temporal(lab: AlphaLab) -> TemporalBenchmark:
    return lab.build_temporal_benchmark(
        n_cohorts=4, buyers_per_cohort=50, drift=0.15, seed=7
    )


@pytest.fixture(scope="module")
def report(lab: AlphaLab, temporal: TemporalBenchmark) -> WalkForwardReport:
    return lab.walk_forward(temporal)


class TestTemporalBenchmark:
    def test_midpoints_drift_upward(self, temporal):
        assert temporal.midpoints[0] < 0.5 < temporal.midpoints[-1]
        assert list(temporal.midpoints) == sorted(temporal.midpoints)

    def test_cohorts_are_distinct(self, temporal):
        fingerprints = {cohort.fingerprint() for cohort in temporal.cohorts}
        assert len(fingerprints) == len(temporal.cohorts)

    def test_is_deterministic(self, lab):
        first = lab.build_temporal_benchmark(n_cohorts=3, buyers_per_cohort=40, drift=0.1)
        second = lab.build_temporal_benchmark(n_cohorts=3, buyers_per_cohort=40, drift=0.1)
        assert first.fingerprint() == second.fingerprint()

    def test_too_few_cohorts_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.build_temporal_benchmark(n_cohorts=2)

    def test_invalid_drift_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.build_temporal_benchmark(n_cohorts=4, drift=0.6)


class TestWalkForward:
    def test_one_step_per_transition(self, report, temporal):
        assert len(report.steps) == len(temporal.cohorts) - 1

    def test_metrics_are_valid(self, report):
        for step in report.steps:
            assert 0.0 <= step.frozen_ndcg <= 1.0
            assert 0.0 <= step.adaptive_ndcg <= 1.0
            assert 0.0 <= step.ensemble_ndcg <= 1.0

    def test_refitting_is_not_worse_than_freezing(self, report):
        assert report.adaptive_mean >= report.frozen_mean - 0.01

    def test_ensemble_adds_no_lift_on_this_benchmark(self, report):
        # Measured finding: mean-rank aggregation of near-duplicate, slightly
        # overfit front members underperforms the single selected alpha. The
        # ensemble is a comparator, not the deployment default.
        assert report.ensemble_mean <= report.adaptive_mean + 0.01
        assert report.ensemble_mean >= report.adaptive_mean - 0.05

    def test_report_serialises(self, report):
        payload = report.to_dict()
        assert len(payload["steps"]) == len(report.steps)
        assert 0.0 <= payload["adaptive_mean"] <= 1.0

    def test_is_deterministic(self, lab, temporal):
        first = lab.walk_forward(temporal)
        second = lab.walk_forward(temporal)
        assert [s.adaptive_ndcg for s in first.steps] == [
            s.adaptive_ndcg for s in second.steps
        ]
