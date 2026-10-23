"""Tests for seed sensitivity: how much of the alpha gain is search-seed luck.

The measured gain ``evolved - baseline`` is produced by a stochastic search, so
part of it may be the luck of one RNG stream rather than a property of the
procedure. Holding the benchmark fixed and varying only the search seed
isolates that component.

Falsifiable predictions:
- With the benchmark fixed, the baseline NDCG is identical on every seed, so
  all observed variation is attributable to the search.
- The gain survives its unluckiest seed, i.e. the reported improvement is not a
  single favourable draw.
- The report is deterministic, aggregates match its own trials, and degenerate
  seed lists are rejected.
"""

from __future__ import annotations

import json
import statistics

import pytest

from acquisition_platform.alpha_lab import (
    AlphaLab,
    MatchingBenchmark,
    SeedSensitivityReport,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError

SEEDS: tuple[int, ...] = (1, 2, 3)


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=24, generations=12)


@pytest.fixture(scope="module")
def matching_benchmark(lab: AlphaLab) -> MatchingBenchmark:
    return lab.build_benchmark(n_buyers=60, sellers_per_buyer=10, seed=7)


@pytest.fixture(scope="module")
def report(lab: AlphaLab, matching_benchmark: MatchingBenchmark) -> SeedSensitivityReport:
    return lab.seed_sensitivity(SEEDS, n_buyers=60, sellers_per_buyer=10)


class TestTrialAccounting:
    def test_one_trial_per_usable_seed(self, report):
        assert report.requested_seeds == SEEDS
        assert report.unusable_seeds == ()
        assert report.n_seeds == len(SEEDS)
        assert [trial.seed for trial in report.trials] == list(SEEDS)

    def test_trials_plus_unusable_account_for_every_request(self, report):
        assert len(report.trials) + len(report.unusable_seeds) == len(
            report.requested_seeds
        )

    def test_benchmark_is_held_fixed(self, report, matching_benchmark):
        assert report.benchmark_fingerprint == matching_benchmark.fingerprint()

    def test_baseline_is_seed_invariant(self, report):
        baselines = {trial.baseline_ndcg for trial in report.trials}
        assert len(baselines) == 1
        assert report.baseline_ndcg == pytest.approx(next(iter(baselines)))

    def test_every_trial_beats_the_baseline(self, report):
        assert all(trial.delta > 0.0 for trial in report.trials)

    def test_delta_is_the_difference_of_its_parts(self, report):
        for trial in report.trials:
            assert trial.delta == pytest.approx(
                trial.evolved_ndcg - trial.baseline_ndcg
            )

    def test_metrics_are_valid_ndcg(self, report):
        for trial in report.trials:
            assert 0.0 <= trial.baseline_ndcg <= 1.0
            assert 0.0 <= trial.evolved_ndcg <= 1.0

    def test_recovered_weights_live_on_the_simplex(self, report):
        for trial in report.trials:
            assert sum(trial.recovered_weights.values()) == pytest.approx(1.0)
            assert all(value >= 0.0 for value in trial.recovered_weights.values())


class TestAggregates:
    def test_mean_and_spread_match_the_trials(self, report):
        deltas = [trial.delta for trial in report.trials]
        assert report.mean_delta == pytest.approx(statistics.fmean(deltas))
        assert report.std_delta == pytest.approx(statistics.pstdev(deltas))
        assert report.min_delta == pytest.approx(min(deltas))
        assert report.max_delta == pytest.approx(max(deltas))

    def test_evolved_ndcg_aggregates_match_the_trials(self, report):
        evolved = [trial.evolved_ndcg for trial in report.trials]
        assert report.mean_evolved_ndcg == pytest.approx(statistics.fmean(evolved))
        assert report.std_evolved_ndcg == pytest.approx(statistics.pstdev(evolved))

    def test_win_rate_counts_positive_gains(self, report):
        deltas = [trial.delta for trial in report.trials]
        assert report.win_rate == pytest.approx(
            sum(1 for delta in deltas if delta > 0.0) / len(deltas)
        )
        assert report.win_rate == 1.0

    def test_confidence_interval_brackets_the_mean(self, report):
        assert report.gain_ci.low <= report.mean_delta <= report.gain_ci.high
        assert report.gain_ci.confidence == pytest.approx(0.95)

    def test_seed_luck_ratio_is_noise_over_signal(self, report):
        assert report.seed_luck_ratio == pytest.approx(
            report.std_delta / report.mean_delta
        )
        assert report.seed_luck_ratio < 1.0

    def test_unlucky_gain_haircuts_one_standard_deviation(self, report):
        assert report.unlucky_gain == pytest.approx(
            report.mean_delta - report.std_delta
        )

    def test_gain_survives_the_unluckiest_seed(self, report):
        assert report.min_delta > 0.0
        assert report.gain_survives_worst_seed is True
        assert report.unlucky_gain > 0.0

    def test_max_param_deviation_is_the_widest_departure(self, report):
        names = ("gap_weight", "midpoint_weight", "size_weight")
        centre = {
            name: statistics.fmean(
                trial.recovered_weights[name] for trial in report.trials
            )
            for name in names
        }
        deviations = [
            sum(abs(trial.recovered_weights[name] - centre[name]) for name in names)
            for trial in report.trials
        ]
        assert report.max_param_deviation == pytest.approx(max(deviations))
        assert report.max_param_deviation >= 0.0

    def test_p_value_is_a_probability(self, report):
        assert 0.0 <= report.p_value <= 1.0


class TestContract:
    def test_analysis_is_deterministic(self, lab):
        first = lab.seed_sensitivity(SEEDS, n_buyers=60, sellers_per_buyer=10)
        second = lab.seed_sensitivity(SEEDS, n_buyers=60, sellers_per_buyer=10)
        assert [t.delta for t in first.trials] == [t.delta for t in second.trials]
        assert first.max_param_deviation == second.max_param_deviation

    def test_report_serialises(self, report):
        payload = json.loads(json.dumps(report.to_dict()))
        assert payload["n_seeds"] == len(SEEDS)
        assert len(payload["trials"]) == len(SEEDS)
        assert payload["mean_delta"] == pytest.approx(report.mean_delta)
        assert payload["gain_ci"]["confidence"] == pytest.approx(0.95)
        assert set(payload["trials"][0]) == {
            "seed",
            "baseline_ndcg",
            "evolved_ndcg",
            "delta",
            "recovered_weights",
            "weight_error_l1",
        }

    def test_empty_seed_list_raises(self, lab):
        with pytest.raises(ValidationError):
            lab.seed_sensitivity((), n_buyers=60, sellers_per_buyer=10)

    def test_single_seed_raises(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.seed_sensitivity((1,), n_buyers=60, sellers_per_buyer=10)

    def test_duplicate_seeds_raise(self, lab):
        with pytest.raises(InvalidRangeError):
            lab.seed_sensitivity((1, 1, 2), n_buyers=60, sellers_per_buyer=10)

    def test_unusable_seed_is_counted_not_fatal(self, lab, monkeypatch):
        original = AlphaLab.evolve_matching_policy

        def degenerate(self, benchmark, seed=None):
            if seed == 5:
                raise ValidationError(
                    "at least one policy weight must be positive"
                )
            return original(self, benchmark, seed=seed)

        monkeypatch.setattr(AlphaLab, "evolve_matching_policy", degenerate)
        report = lab.seed_sensitivity((4, 5, 6), n_buyers=12, sellers_per_buyer=3)
        assert report.unusable_seeds == (5,)
        assert [trial.seed for trial in report.trials] == [4, 6]
        assert report.n_seeds == 2
        assert report.mean_delta == pytest.approx(
            statistics.fmean(trial.delta for trial in report.trials)
        )

    def test_unrelated_failure_propagates(self, lab, monkeypatch):
        original = AlphaLab.evolve_matching_policy

        def broken(self, benchmark, seed=None):
            if seed == 5:
                raise ValidationError("objectives missing for evolution")
            return original(self, benchmark, seed=seed)

        monkeypatch.setattr(AlphaLab, "evolve_matching_policy", broken)
        with pytest.raises(ValidationError, match="objectives missing"):
            lab.seed_sensitivity((4, 5, 6), n_buyers=12, sellers_per_buyer=3)

    def test_too_few_usable_seeds_raises(self, lab, monkeypatch):
        def always_degenerate(self, benchmark, seed=None):
            raise ValidationError("at least one policy weight must be positive")

        monkeypatch.setattr(
            AlphaLab, "evolve_matching_policy", always_degenerate
        )
        with pytest.raises(ValidationError, match="usable"):
            lab.seed_sensitivity((1, 2), n_buyers=12, sellers_per_buyer=3)


class TestMisspecifiedRegime:
    def test_quality_weight_is_recorded(self, lab):
        report = lab.seed_sensitivity(
            (1, 2), n_buyers=40, sellers_per_buyer=8, quality_weight=0.6
        )
        assert report.quality_weight == pytest.approx(0.6)

    def test_search_cannot_saturate_when_truth_is_unobservable(self, lab):
        report = lab.seed_sensitivity(
            (1, 2), n_buyers=40, sellers_per_buyer=8, quality_weight=0.6
        )
        assert report.mean_evolved_ndcg < 0.99
