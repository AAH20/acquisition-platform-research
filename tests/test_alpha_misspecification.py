"""Tests for misspecification, oracle comparison, and rank stability.

Falsifiable predictions:
- When the true utility depends on a signal the policy cannot observe, the
  evolved policy must NOT reach the NDCG ceiling, yet must still beat the
  legacy heuristic.
- A dense grid search must find at least as good a training policy as the
  evolver on the smooth default benchmark.
- Small price perturbations must leave the ranking largely intact.
"""

from __future__ import annotations

import pytest

from acquisition_platform.alpha_lab import AlphaLab, MatchingBenchmark
from acquisition_platform.exceptions import InvalidRangeError


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=20, generations=10)


@pytest.fixture(scope="module")
def matching_benchmark(lab: AlphaLab) -> MatchingBenchmark:
    return lab.build_benchmark(n_buyers=60, sellers_per_buyer=10, seed=7)


class TestMisspecification:
    def test_default_benchmark_is_unchanged(self, lab, matching_benchmark):
        """Adding the quality knob must not alter the default benchmark."""
        again = lab.build_benchmark(n_buyers=60, sellers_per_buyer=10, seed=7)
        assert matching_benchmark.fingerprint() == again.fingerprint()

    def test_unobservable_signal_caps_achievable_ndcg(self, lab):
        report = lab.misspecification_study(quality_weight=0.6, n_buyers=48)
        assert report.evolved_ndcg < 0.97

    def test_evolved_still_beats_baseline_under_misspecification(self, lab):
        report = lab.misspecification_study(quality_weight=0.6, n_buyers=48)
        assert report.evolved_ndcg > report.baseline_ndcg + 0.05

    def test_utility_regret_shrinks(self, lab):
        report = lab.misspecification_study(quality_weight=0.6, n_buyers=48)
        assert report.evolved_regret < report.baseline_regret

    def test_study_is_deterministic(self, lab):
        first = lab.misspecification_study(quality_weight=0.6, n_buyers=48)
        second = lab.misspecification_study(quality_weight=0.6, n_buyers=48)
        assert first.evolved_ndcg == second.evolved_ndcg
        assert first.evolved_regret == second.evolved_regret

    def test_report_serialises(self, lab):
        payload = lab.misspecification_study(
            quality_weight=0.6, n_buyers=48
        ).to_dict()
        assert payload["quality_weight"] == 0.6
        assert 0.0 <= payload["evolved_ndcg"] <= 1.0

    def test_invalid_quality_weight_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.build_benchmark(n_buyers=48, quality_weight=-0.5)


class TestGridOracle:
    def test_grid_search_is_deterministic(self, lab, matching_benchmark):
        first = lab.grid_search_baseline(matching_benchmark, steps=4)
        second = lab.grid_search_baseline(matching_benchmark, steps=4)
        assert first == second

    def test_grid_accounts_for_every_point(self, lab, matching_benchmark):
        result = lab.grid_search_baseline(matching_benchmark, steps=4)
        assert result["evaluations"] == 4**3 - 1

    def test_grid_reaches_ceiling_on_default_benchmark(self, lab, matching_benchmark):
        result = lab.grid_search_baseline(matching_benchmark, steps=8)
        assert result["test_ndcg@5"] > 0.99

    def test_grid_respects_search_space(self, lab, matching_benchmark):
        result = lab.grid_search_baseline(matching_benchmark, steps=4)
        assert 0.0 <= result["params"]["gap_weight"] <= 1.0
        assert 0.0 <= result["params"]["midpoint_weight"] <= 1.0
        assert 0.0 <= result["params"]["size_weight"] <= 1.0

    def test_too_coarse_grid_raises(self, lab, matching_benchmark):
        with pytest.raises(InvalidRangeError):
            lab.grid_search_baseline(matching_benchmark, steps=1)


class TestRankStability:
    def test_small_noise_preserves_ranking(self, lab):
        evolution = lab.evolve_matching_policy(
            lab.build_benchmark(n_buyers=48, sellers_per_buyer=10, seed=7)
        )
        report = lab.stability_under_noise(
            evolution.selected_alpha.params, sigma=0.05, trials=3
        )
        assert report.mean_spearman > 0.95

    def test_stability_is_deterministic(self, lab):
        evolution = lab.evolve_matching_policy(
            lab.build_benchmark(n_buyers=48, sellers_per_buyer=10, seed=7)
        )
        first = lab.stability_under_noise(
            evolution.selected_alpha.params, sigma=0.05, trials=2
        )
        second = lab.stability_under_noise(
            evolution.selected_alpha.params, sigma=0.05, trials=2
        )
        assert first.mean_spearman == second.mean_spearman

    def test_report_serialises(self, lab):
        evolution = lab.evolve_matching_policy(
            lab.build_benchmark(n_buyers=48, sellers_per_buyer=10, seed=7)
        )
        payload = lab.stability_under_noise(
            evolution.selected_alpha.params, sigma=0.05, trials=2
        ).to_dict()
        assert -1.0 <= payload["mean_spearman"] <= 1.0
        assert payload["trials"] == 2

    def test_invalid_sigma_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.stability_under_noise(
                {"gap_weight": 1.0, "midpoint_weight": 0.0, "size_weight": 0.0},
                sigma=1.5,
            )
