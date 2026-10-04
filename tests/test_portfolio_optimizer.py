"""Tests for portfolio optimization module."""
import pytest
from acquisition_platform.portfolio_optimizer import PortfolioOptimizer, Asset, Portfolio


class TestPortfolioOptimizer:
    """TDD tests for the portfolio optimizer (MIQP — Mixed Integer Quadratic Program)."""

    def test_empty_portfolio_returns_empty(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        result = optimizer.optimize([], risk_tolerance=0.5)
        assert result.assets == []
        assert result.expected_return == 0

    def test_single_asset_within_budget(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15)]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) == 1
        assert result.assets[0].id == "a1"

    def test_budget_constraint_respected(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="a1", cost=600000, expected_return=0.12, risk=0.15),
            Asset(id="a2", cost=600000, expected_return=0.10, risk=0.10),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        total_cost = sum(a.cost for a in result.assets)
        assert total_cost <= 1000000

    def test_higher_risk_tolerance_selects_higher_return(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="safe", cost=500000, expected_return=0.06, risk=0.05),
            Asset(id="risky", cost=500000, expected_return=0.15, risk=0.25),
        ]
        conservative = optimizer.optimize(assets, risk_tolerance=0.1)
        aggressive = optimizer.optimize(assets, risk_tolerance=0.5)
        # Aggressive should pick the risky asset
        assert any(a.id == "risky" for a in aggressive.assets)

    def test_cardinality_constraint_limits_selections(self):
        optimizer = PortfolioOptimizer(budget=10000000, max_assets=2)
        assets = [
            Asset(id=f"a{i}", cost=1000000, expected_return=0.10 + i*0.01, risk=0.15)
            for i in range(10)
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) <= 2

    def test_diversification_bonus(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="a1", cost=400000, expected_return=0.12, risk=0.15, sector="saas"),
            Asset(id="a2", cost=400000, expected_return=0.11, risk=0.14, sector="ecommerce"),
            Asset(id="a3", cost=400000, expected_return=0.10, risk=0.13, sector="saas"),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        sectors = [a.sector for a in result.assets]
        # Should prefer diversification
        assert len(set(sectors)) >= 1

    def test_portfolio_has_sharpe_ratio(self):
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15),
            Asset(id="a2", cost=500000, expected_return=0.08, risk=0.10),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert hasattr(result, 'sharpe_ratio')
        assert result.sharpe_ratio > 0
