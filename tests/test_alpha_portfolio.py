"""Tests for the portfolio domain — the same evolver, a different problem.

Falsifiable predictions:
- Policy weights always sum to one and respect the per-asset cap.
- The analytic oracle beats naive baselines.
- The shared evolver beats both naive baselines and lands close to the oracle.
- The Pareto front is non-trivial and its hypervolume is positive.
"""

from __future__ import annotations

import pytest

from acquisition_platform.alpha_portfolio import (
    PortfolioLab,
    PortfolioReport,
    policy_weights,
    portfolio_stats,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError


@pytest.fixture(scope="module")
def lab() -> PortfolioLab:
    return PortfolioLab(seed=7, population_size=40, generations=25)


@pytest.fixture(scope="module")
def market(lab: PortfolioLab):
    return lab.build_market(n_assets=8, n_sectors=3, seed=7)


@pytest.fixture(scope="module")
def report(lab: PortfolioLab, market) -> PortfolioReport:
    return lab.evolve(market)


class TestPolicy:
    def test_weights_sum_to_one(self, market):
        weights = policy_weights(
            {"return_tilt": 1.2, "risk_penalty": 0.8, "sector_tilt": 0.4}, market, 0.35
        )
        assert sum(weights) == pytest.approx(1.0)

    def test_weights_respect_cap(self, market):
        weights = policy_weights(
            {"return_tilt": 3.0, "risk_penalty": 0.0, "sector_tilt": 0.0}, market, 0.35
        )
        assert max(weights) <= 0.35 + 1e-9

    def test_zero_tilt_is_equal_weight(self, market):
        weights = policy_weights(
            {"return_tilt": 0.0, "risk_penalty": 0.0, "sector_tilt": 0.0}, market, 0.35
        )
        assert all(weight == pytest.approx(1.0 / market.size) for weight in weights)

    def test_higher_risk_penalty_favours_low_volatility(self, market):
        low = policy_weights(
            {"return_tilt": 0.0, "risk_penalty": 0.0, "sector_tilt": 0.0}, market, 0.35
        )
        high = policy_weights(
            {"return_tilt": 0.0, "risk_penalty": 2.0, "sector_tilt": 0.0}, market, 0.35
        )
        calmest = min(range(market.size), key=lambda i: market.assets[i].volatility)
        assert high[calmest] > low[calmest]

    def test_rejects_wrong_length(self, market):
        with pytest.raises(ValidationError):
            portfolio_stats([0.5, 0.5], market)


class TestBaselines:
    def test_equal_weight_is_uniform(self, market):
        stats = portfolio_stats([1.0 / market.size] * market.size, market)
        assert stats.weights == pytest.approx((1.0 / market.size,) * market.size)

    def test_oracle_beats_equal_weight(self, report):
        assert report.oracle.sharpe > report.equal_weight.sharpe

    def test_diversification_in_unit_interval(self, report):
        for allocation in (
            report.evolved,
            report.equal_weight,
            report.inverse_volatility,
            report.oracle,
        ):
            assert 0.0 <= allocation.diversification <= 1.0


class TestEvolution:
    def test_beats_naive_baselines(self, report):
        assert report.evolved.sharpe > report.equal_weight.sharpe
        assert report.evolved.sharpe > report.inverse_volatility.sharpe

    def test_approaches_the_analytic_oracle(self, report):
        assert report.share_of_oracle > 0.95

    def test_pareto_front_is_non_trivial(self, report):
        assert report.pareto_size > 1

    def test_hypervolume_is_positive(self, report):
        assert report.hypervolume is not None
        assert report.hypervolume > 0.0

    def test_is_deterministic(self, lab, market):
        first = lab.evolve(market)
        second = lab.evolve(market)
        assert first.evolved.sharpe == second.evolved.sharpe
        assert first.evaluations == second.evaluations

    def test_report_serialises(self, report):
        payload = report.to_dict()
        assert len(payload["evolved"]["weights"]) == 8  # type: ignore[arg-type]
        assert payload["share_of_oracle"] > 0.0


class TestValidation:
    def test_rejects_infeasible_cap(self):
        with pytest.raises(InvalidRangeError):
            PortfolioLab(max_weight=0.05).build_market(n_assets=8)

    def test_rejects_bad_correlation(self):
        from acquisition_platform.alpha_portfolio import Asset, Market

        assets = (
            Asset("a", 0.05, 0.20, 0),
            Asset("b", 0.06, 0.25, 0),
        )
        with pytest.raises(InvalidRangeError):
            Market(assets=assets, within_sector_correlation=2.0)

    def test_market_fingerprint_is_stable(self, lab):
        first = lab.build_market(seed=11)
        second = lab.build_market(seed=11)
        assert first.fingerprint() == second.fingerprint()
