"""Tests for the third domain: first-price bid shading under sampling noise.

The two earlier domains are both maximised against an objective that can be
computed exactly (a sampled matching benchmark with a large buyer pool, and an
analytic mean-variance market). This domain is deliberately harder: the
objective handed to the evolver is a *finite-sample estimate* of expected
profit, so candidate rankings are noisy.

Falsifiable predictions:

- The policy family contains the symmetric Bayes-Nash equilibrium
  ``b(v) = ((n-1)/n) v`` and its profit/win-rate pair matches the closed form
  ``1/(n(n+1))`` and ``1/n``.
- A single evaluation really is noisy: the standard deviation of independent
  300-auction estimates is within a factor of two of ``sigma/sqrt(300)`` and
  falls as the sample grows.
- The shared :class:`AlphaEvolver` recovers at least 90% of the closed-form
  equilibrium profit despite only ever seeing noisy estimates.
- The scalarised best alpha does *not* maximise profit (it buys win rate), so
  the deployment candidate must be picked from the Pareto front by an explicit
  rule. This is asserted, not glossed over.
"""

from __future__ import annotations

import math

import pytest

from acquisition_platform.alpha_auction import (
    GRID_CURVES,
    GRID_SHADES,
    GRID_TILTS,
    PARAM_NAMES,
    AuctionLab,
    AuctionMarket,
    AuctionReport,
    ExperimentBudget,
    bid_for_value,
    equilibrium_params,
    grid_search,
    sample_auctions,
    score_policy,
    truthful_params,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError

LARGE_SEED = 2024


@pytest.fixture(scope="module")
def market() -> AuctionMarket:
    return AuctionMarket(n_bidders=4)


@pytest.fixture(scope="module")
def large_sample(market: AuctionMarket):
    return sample_auctions(market, size=20000, seed=LARGE_SEED)


@pytest.fixture(scope="module")
def lab() -> AuctionLab:
    return AuctionLab(seed=7)


@pytest.fixture(scope="module")
def report(lab: AuctionLab, market: AuctionMarket) -> AuctionReport:
    return lab.run(market)


def equilibrium_win_rate_proportion(n_bidders: int) -> float:
    """Closed-form win rate of the symmetric equilibrium policy."""
    return 1.0 / n_bidders


class TestMarket:
    def test_rival_shade_is_the_equilibrium_slope(self, market: AuctionMarket) -> None:
        assert market.rival_shade == pytest.approx(0.75)

    def test_equilibrium_profit_closed_form(self, market: AuctionMarket) -> None:
        assert market.equilibrium_profit == pytest.approx(1.0 / 20.0)

    def test_equilibrium_win_rate_closed_form(self, market: AuctionMarket) -> None:
        assert market.equilibrium_win_rate == pytest.approx(0.25)

    def test_two_bidder_market(self) -> None:
        duopoly = AuctionMarket(n_bidders=2)
        assert duopoly.rival_shade == pytest.approx(0.5)
        assert duopoly.equilibrium_profit == pytest.approx(1.0 / 6.0)

    def test_rejects_single_bidder(self) -> None:
        with pytest.raises(InvalidRangeError):
            AuctionMarket(n_bidders=1)

    def test_fingerprint_is_stable_and_market_specific(
        self, market: AuctionMarket
    ) -> None:
        assert market.fingerprint() == AuctionMarket(n_bidders=4).fingerprint()
        assert market.fingerprint() != AuctionMarket(n_bidders=5).fingerprint()


class TestPolicy:
    def test_bids_increase_with_value(self, market: AuctionMarket) -> None:
        params = equilibrium_params(market)
        bids = [bid_for_value(value / 20.0, params) for value in range(1, 20)]
        assert bids == sorted(bids)
        assert bids[-1] > bids[0]

    def test_zero_value_bids_nothing(self, market: AuctionMarket) -> None:
        assert bid_for_value(0.0, equilibrium_params(market)) == pytest.approx(0.0)

    def test_equilibrium_policy_shades_linearly(self, market: AuctionMarket) -> None:
        params = equilibrium_params(market)
        for value in (0.1, 0.45, 0.9):
            assert bid_for_value(value, params) == pytest.approx(0.75 * value)

    def test_truthful_policy_equals_value(self) -> None:
        params = truthful_params()
        for value in (0.1, 0.45, 0.9):
            assert bid_for_value(value, params) == pytest.approx(value)

    def test_tilt_raises_low_value_bids(self, market: AuctionMarket) -> None:
        base = {"shade": 0.75, "curve": 1.0, "low_value_tilt": 0.0}
        tilted = {"shade": 0.75, "curve": 1.0, "low_value_tilt": 0.5}
        assert bid_for_value(0.2, tilted) > bid_for_value(0.2, base)
        assert bid_for_value(0.2, tilted) == pytest.approx(0.75 * 0.2 * 1.4)

    def test_bids_stay_non_negative_at_the_extreme_tilt(
        self, market: AuctionMarket
    ) -> None:
        params = {"shade": 0.4, "curve": 0.8, "low_value_tilt": -0.6}
        assert all(bid_for_value(value / 50.0, params) >= 0.0 for value in range(51))

    def test_rejects_missing_gene(self, market: AuctionMarket) -> None:
        with pytest.raises(ValidationError):
            bid_for_value(0.5, {"shade": 0.75, "curve": 1.0})

    def test_rejects_out_of_range_value(self, market: AuctionMarket) -> None:
        with pytest.raises(InvalidRangeError):
            bid_for_value(1.5, equilibrium_params(market))

    def test_param_names_are_the_three_genes(self) -> None:
        assert PARAM_NAMES == ("shade", "curve", "low_value_tilt")
        assert set(equilibrium_params(AuctionMarket())) == set(PARAM_NAMES)


class TestSample:
    def test_size_and_bounds(self, market: AuctionMarket, large_sample) -> None:
        assert large_sample.size == 20000
        assert len(large_sample.values) == len(large_sample.rival_bids)
        assert all(0.0 <= value <= 1.0 for value in large_sample.values[:500])
        cap = market.rival_shade
        assert all(0.0 <= bid <= cap for bid in large_sample.rival_bids)

    def test_is_deterministic(self, market: AuctionMarket) -> None:
        first = sample_auctions(market, size=25, seed=3)
        second = sample_auctions(market, size=25, seed=3)
        assert first.values == second.values
        assert first.fingerprint() == second.fingerprint()

    def test_different_seeds_give_different_transcripts(
        self, market: AuctionMarket
    ) -> None:
        assert (
            sample_auctions(market, size=25, seed=3).values
            != sample_auctions(market, size=25, seed=4).values
        )

    def test_rejects_empty_size(self, market: AuctionMarket) -> None:
        with pytest.raises(InvalidRangeError):
            sample_auctions(market, size=0, seed=1)


class TestAnalyticGroundTruth:
    """The closed forms are the oracle; the simulator must reproduce them."""

    def test_equilibrium_profit_matches_closed_form(
        self, market: AuctionMarket, large_sample
    ) -> None:
        outcome = score_policy(equilibrium_params(market), large_sample)
        assert abs(outcome.profit - market.equilibrium_profit) < 3.0 * outcome.std_error

    def test_equilibrium_win_rate_matches_closed_form(
        self, market: AuctionMarket, large_sample
    ) -> None:
        outcome = score_policy(equilibrium_params(market), large_sample)
        expected = equilibrium_win_rate_proportion(market.n_bidders)
        tolerance = 3.0 * math.sqrt(expected * (1.0 - expected) / large_sample.size)
        assert abs(outcome.win_rate - expected) < tolerance

    def test_truthful_bidding_earns_nothing(
        self, market: AuctionMarket, large_sample
    ) -> None:
        outcome = score_policy(truthful_params(), large_sample)
        assert outcome.profit == pytest.approx(0.0, abs=1e-12)

    def test_truthful_bidding_wins_more_often(self, large_sample) -> None:
        # P(win) = 1 - c + c/n = 0.4375 for n = 4: paying full value buys a
        # higher win rate and zero profit, so win rate is a poor profit proxy.
        outcome = score_policy(truthful_params(), large_sample)
        expected = 1.0 - 0.75 + 0.75 / 4.0
        tolerance = 3.0 * math.sqrt(expected * (1.0 - expected) / large_sample.size)
        assert abs(outcome.win_rate - expected) < tolerance

    def test_no_grid_shade_beats_the_equilibrium_slope(
        self, market: AuctionMarket, large_sample
    ) -> None:
        best = score_policy(equilibrium_params(market), large_sample)
        for shade in GRID_SHADES:
            params = {"shade": shade, "curve": 1.0, "low_value_tilt": 0.0}
            candidate = score_policy(params, large_sample)
            assert candidate.profit <= best.profit + 3.0 * best.std_error

    def test_equilibrium_beats_truthful_and_overbidding(
        self, market: AuctionMarket, large_sample
    ) -> None:
        best = score_policy(equilibrium_params(market), large_sample)
        assert best.profit > score_policy(truthful_params(), large_sample).profit
        aggressive = {"shade": 0.95, "curve": 1.0, "low_value_tilt": 0.0}
        assert best.profit > score_policy(aggressive, large_sample).profit


class TestNoise:
    def test_repeated_estimates_disagree(self, lab: AuctionLab, market: AuctionMarket) -> None:
        estimates = {
            lab.evaluate(equilibrium_params(market), market, draw=draw)["profit"]
            for draw in range(8)
        }
        assert len(estimates) > 1

    def test_noise_shrinks_with_the_sample(self, lab: AuctionLab, market: AuctionMarket) -> None:
        small = lab.estimate_noise(equilibrium_params(market), market, draws=40)
        large = AuctionLab(
            seed=7, budget=ExperimentBudget(sample_size=2400, validation_size=2400, audit_size=2400)
        ).estimate_noise(equilibrium_params(market), market, draws=40)
        assert small.relative_noise > large.relative_noise
        assert small.stdev_profit > large.stdev_profit

    def test_noise_matches_the_standard_error(
        self, lab: AuctionLab, market: AuctionMarket
    ) -> None:
        # sd of independent estimates ~= sigma / sqrt(n); with sigma ~= 0.089
        # and n = 300 the predicted sd is ~0.0051, i.e. ~10% of the 0.05 mean.
        profile = lab.estimate_noise(equilibrium_params(market), market, draws=60)
        assert profile.mean_profit == pytest.approx(market.equilibrium_profit, abs=0.004)
        assert profile.stdev_profit == pytest.approx(0.0051, rel=0.35)
        assert profile.relative_noise > 0.04

    def test_estimate_is_reproducible(self, lab: AuctionLab, market: AuctionMarket) -> None:
        first = lab.evaluate(equilibrium_params(market), market, draw=5)
        second = lab.evaluate(equilibrium_params(market), market, draw=5)
        assert first == second


class TestGridOracle:
    def test_returns_a_grid_point(self, market: AuctionMarket) -> None:
        params = grid_search(sample_auctions(market, size=400, seed=31))
        assert params["shade"] in GRID_SHADES
        assert params["curve"] in GRID_CURVES
        assert params["low_value_tilt"] in GRID_TILTS

    def test_grid_covers_the_equilibrium_point(self) -> None:
        assert 0.75 in GRID_SHADES
        assert 1.0 in GRID_CURVES
        assert 0.0 in GRID_TILTS

    def test_grid_finds_the_equilibrium_neighbourhood(
        self, market: AuctionMarket
    ) -> None:
        params = grid_search(sample_auctions(market, size=4000, seed=101))
        assert abs(params["shade"] - market.rival_shade) <= 0.06

    def test_grid_profit_is_near_the_closed_form(
        self, market: AuctionMarket, large_sample
    ) -> None:
        params = grid_search(sample_auctions(market, size=4000, seed=101))
        outcome = score_policy(params, large_sample)
        assert outcome.profit > 0.9 * market.equilibrium_profit

    def test_grid_search_is_deterministic(self, market: AuctionMarket) -> None:
        sample = sample_auctions(market, size=300, seed=77)
        assert grid_search(sample) == grid_search(sample)


class TestEvolution:
    def test_never_loses_money(self, report: AuctionReport) -> None:
        assert report.evolved.profit > 0.0

    def test_beats_truthful_bidding(self, report: AuctionReport) -> None:
        assert report.evolved.profit > report.truthful.profit

    def test_recovers_the_equilibrium_profit(self, report: AuctionReport) -> None:
        assert report.share_of_equilibrium > 0.90

    def test_win_rate_is_a_probability(self, report: AuctionReport) -> None:
        for outcome in (report.evolved, report.truthful, report.equilibrium):
            assert 0.0 <= outcome.win_rate <= 1.0

    def test_matches_or_beats_a_coarse_grid_search(self, report: AuctionReport) -> None:
        assert report.evolved.profit >= 0.95 * report.grid_oracle.profit

    def test_pareto_front_is_non_trivial(self, report: AuctionReport) -> None:
        assert report.pareto_size > 1

    def test_hypervolume_is_positive(self, report: AuctionReport) -> None:
        assert report.hypervolume is not None
        assert report.hypervolume > 0.0

    def test_scalar_best_trades_profit_for_win_rate(self, report: AuctionReport) -> None:
        # Measured finding: the highest-fitness alpha is the win-rate corner,
        # not the profit optimum. Selection from the front must be explicit.
        assert report.scalar_best.win_rate > report.evolved.win_rate
        assert report.scalar_best.profit < report.evolved.profit

    def test_evaluation_count_reflects_the_budget(self, report: AuctionReport) -> None:
        assert report.evaluations > 200
        assert report.elapsed_seconds > 0.0

    def test_is_deterministic(self, market: AuctionMarket) -> None:
        lab = AuctionLab(
            seed=11,
            population_size=12,
            generations=6,
            budget=ExperimentBudget(sample_size=150, validation_size=300, grid_size=300, audit_size=600),
        )
        first = lab.run(market)
        second = lab.run(market)
        assert first.evolved.profit == second.evolved.profit
        assert first.evaluations == second.evaluations
        assert first.pareto_size == second.pareto_size

    def test_report_serialises(self, report: AuctionReport) -> None:
        payload = report.to_dict()
        assert set(payload) >= {
            "evolved",
            "truthful",
            "equilibrium",
            "grid_oracle",
            "scalar_best",
            "share_of_equilibrium",
            "pareto_size",
            "hypervolume",
            "evaluations",
            "seed",
        }
        assert payload["evolved"]["profit"] > 0.0  # type: ignore[index]

    def test_seed_sweep_is_centred_on_the_equilibrium(self, market: AuctionMarket) -> None:
        lab = AuctionLab(
            seed=3,
            population_size=16,
            generations=10,
            budget=ExperimentBudget(sample_size=200, validation_size=600, grid_size=600, audit_size=2000),
        )
        summary = lab.seed_sweep(market, seeds=(1, 2, 3))
        assert len(summary.profits) == 3
        assert summary.mean_profit > 0.9 * market.equilibrium_profit
        assert summary.stdev_profit >= 0.0
        assert summary.min_profit <= summary.mean_profit <= summary.max_profit


class TestValidation:
    def test_rejects_tiny_sample(self) -> None:
        with pytest.raises(InvalidRangeError):
            ExperimentBudget(sample_size=1)

    def test_rejects_tiny_population(self) -> None:
        with pytest.raises(InvalidRangeError):
            AuctionLab(population_size=1)

    def test_rejects_bad_generations(self) -> None:
        with pytest.raises(InvalidRangeError):
            AuctionLab(generations=0)

    def test_score_policy_rejects_missing_gene(self, market: AuctionMarket) -> None:
        sample = sample_auctions(market, size=10, seed=1)
        with pytest.raises(ValidationError):
            score_policy({"shade": 0.75, "curve": 1.0}, sample)

    def test_score_policy_rejects_gene_outside_its_box(
        self, market: AuctionMarket
    ) -> None:
        # The grid path (_profit_of) and score_policy must accept exactly the
        # same inputs, so both share one bounds check.
        sample = sample_auctions(market, size=10, seed=1)
        with pytest.raises(InvalidRangeError):
            score_policy({"shade": 1.5, "curve": 1.0, "low_value_tilt": 0.0}, sample)
        with pytest.raises(InvalidRangeError):
            bid_for_value(0.5, {"shade": 0.75, "curve": 1.0, "low_value_tilt": -0.9})
