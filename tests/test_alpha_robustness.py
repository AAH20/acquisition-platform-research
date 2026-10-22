"""Tests for robustness, cross-validation, and search-baseline comparison.

Falsifiable predictions:
- A policy evolved at midpoint 0.5 degrades monotonically as the true
  midpoint moves away from 0.5.
- k-fold cross-validation agrees with the single-split result in sign.
- Random search at the same evaluation budget is deterministic and valid.
"""

from __future__ import annotations

import pytest

from acquisition_platform.alpha_lab import AlphaLab, MatchingBenchmark, compare_search_strategies
from acquisition_platform.exceptions import InvalidRangeError


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=24, generations=12)


@pytest.fixture(scope="module")
def matching_benchmark(lab: AlphaLab) -> MatchingBenchmark:
    return lab.build_benchmark(n_buyers=60, sellers_per_buyer=10, seed=7)


@pytest.fixture(scope="module")
def evolution(lab: AlphaLab, matching_benchmark: MatchingBenchmark):
    return lab.evolve_matching_policy(matching_benchmark)


class TestSpecificationShift:
    def test_curve_covers_requested_offsets(self, lab, evolution):
        curve = lab.robustness_curve(
            evolution.selected_alpha.params, offsets=[0.45, 0.50, 0.55], n_buyers=60
        )
        assert [point.offset for point in curve] == [0.45, 0.50, 0.55]

    def test_metrics_are_valid_probabilities(self, lab, evolution):
        curve = lab.robustness_curve(
            evolution.selected_alpha.params, offsets=[0.50, 0.60], n_buyers=60
        )
        for point in curve:
            assert 0.0 <= point.baseline_ndcg <= 1.0
            assert 0.0 <= point.evolved_ndcg <= 1.0

    def test_degradation_is_monotonic_away_from_training_midpoint(self, lab, evolution):
        curve = lab.robustness_curve(
            evolution.selected_alpha.params,
            offsets=[0.50, 0.60, 0.70],
            n_buyers=60,
        )
        values = [point.evolved_ndcg for point in curve]
        assert values[0] >= values[1] >= values[2]

    def test_curve_is_deterministic(self, lab, evolution):
        first = lab.robustness_curve(
            evolution.selected_alpha.params, offsets=[0.55], n_buyers=60
        )
        second = lab.robustness_curve(
            evolution.selected_alpha.params, offsets=[0.55], n_buyers=60
        )
        assert first[0].evolved_ndcg == second[0].evolved_ndcg

    def test_invalid_offset_raises(self, lab, evolution):
        with pytest.raises(InvalidRangeError):
            lab.robustness_curve(evolution.selected_alpha.params, offsets=[1.5])


class TestCrossValidation:
    def test_reports_one_result_per_fold(self, lab):
        report = lab.cross_validate(n_splits=3, n_buyers=60)
        assert len(report.folds) == 3
        assert report.n_splits == 3

    def test_aggregates_are_consistent(self, lab):
        report = lab.cross_validate(n_splits=3, n_buyers=60)
        deltas = [fold.delta for fold in report.folds]
        assert report.mean_delta == pytest.approx(sum(deltas) / len(deltas))
        assert report.win_rate == pytest.approx(
            sum(1 for delta in deltas if delta > 0) / len(deltas)
        )
        assert report.mean_evolved_ndcg > report.mean_baseline_ndcg

    def test_cross_validation_is_deterministic(self, lab):
        first = lab.cross_validate(n_splits=3, n_buyers=60)
        second = lab.cross_validate(n_splits=3, n_buyers=60)
        assert [f.delta for f in first.folds] == [f.delta for f in second.folds]

    def test_too_few_splits_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.cross_validate(n_splits=1, n_buyers=60)


class TestRandomSearchBaseline:
    def test_returns_valid_metrics(self, lab, matching_benchmark):
        result = lab.random_search_baseline(matching_benchmark, budget=40, seed=3)
        assert 0.0 <= result["test_ndcg@5"] <= 1.0
        assert result["evaluations"] == 40

    def test_is_deterministic(self, lab, matching_benchmark):
        first = lab.random_search_baseline(matching_benchmark, budget=30, seed=5)
        second = lab.random_search_baseline(matching_benchmark, budget=30, seed=5)
        assert first == second

    def test_respects_search_space(self, lab, matching_benchmark):
        result = lab.random_search_baseline(matching_benchmark, budget=30, seed=1)
        assert 0.0 <= result["params"]["gap_weight"] <= 1.0
        assert 0.0 <= result["params"]["midpoint_weight"] <= 1.0
        assert 0.0 <= result["params"]["size_weight"] <= 1.0
        assert -0.2 <= result["params"]["bias"] <= 0.2

    def test_zero_budget_raises(self, lab, matching_benchmark):
        with pytest.raises(InvalidRangeError):
            lab.random_search_baseline(matching_benchmark, budget=0, seed=1)


class TestSearchStrategyComparison:
    def test_evolution_beats_random_on_multimodal_objective(self):
        result = compare_search_strategies(budget=600, seed=7, dimensions=3)
        assert result.evolutionary_best > result.random_best

    def test_comparison_is_deterministic(self):
        first = compare_search_strategies(budget=300, seed=5, dimensions=3)
        second = compare_search_strategies(budget=300, seed=5, dimensions=3)
        assert first.evolutionary_best == second.evolutionary_best
        assert first.random_best == second.random_best

    def test_budget_is_respected(self):
        result = compare_search_strategies(budget=400, seed=3, dimensions=2)
        assert result.random_evals == 400
        assert 380 <= result.evolutionary_evals <= 420

    def test_invalid_budget_raises(self):
        with pytest.raises(InvalidRangeError):
            compare_search_strategies(budget=1, seed=1, dimensions=2)
