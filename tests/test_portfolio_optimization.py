"""Tests for portfolio optimization module (Wave 2)."""
import math

import pytest

from acquisition_platform.portfolio_optimization import (
    Asset,
    Portfolio,
    PortfolioOptimizer,
)


def _sample_assets() -> list[Asset]:
    """Create a diverse set of sample assets."""
    return [
        Asset(name="AAPL", expected_return=0.12, risk=0.18, cost=100.0, category="tech"),
        Asset(name="MSFT", expected_return=0.10, risk=0.15, cost=100.0, category="tech"),
        Asset(name="JPM", expected_return=0.08, risk=0.12, cost=100.0, category="finance"),
        Asset(name="JNJ", expected_return=0.06, risk=0.08, cost=100.0, category="healthcare"),
        Asset(name="XOM", expected_return=0.07, risk=0.14, cost=100.0, category="energy"),
    ]


class TestPortfolioOptimization:
    """TDD tests for portfolio optimization."""

    def test_portfolio_optimization(self):
        """Portfolio is optimized correctly with valid assets."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()
        result = optimizer.optimize(assets, risk_tolerance=0.5, budget=300.0)

        assert isinstance(result, Portfolio)
        assert len(result.assets) > 0
        assert len(result.weights) == len(result.assets)
        assert abs(sum(result.weights) - 1.0) < 1e-6
        assert result.expected_return > 0
        assert result.risk > 0
        assert result.sharpe > 0
        # Budget respected
        total_cost = sum(a.cost for a in result.assets)
        assert total_cost <= 300.0 + 1e-6

    def test_risk_return_tradeoff(self):
        """Risk-return tradeoff is calculated for each asset."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()
        result = optimizer.risk_return_tradeoff(assets)

        assert isinstance(result, dict)
        assert len(result) == len(assets)
        for asset in assets:
            assert asset.name in result
            metrics = result[asset.name]
            assert "return_risk_ratio" in metrics
            assert "expected_return" in metrics
            assert "risk" in metrics
            assert metrics["return_risk_ratio"] > 0

    def test_empty_portfolio(self):
        """Empty portfolio returns defaults."""
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize([], risk_tolerance=0.5, budget=1000.0)

        assert isinstance(result, Portfolio)
        assert result.assets == []
        assert result.weights == []
        assert result.expected_return == 0.0
        assert result.risk == 0.0
        assert result.sharpe == 0.0

    def test_diversification_score(self):
        """Diversification is scored correctly."""
        optimizer = PortfolioOptimizer()

        # Equal weights across 4 categories → high diversification
        weights = [0.25, 0.25, 0.25, 0.25]
        categories = ["tech", "finance", "healthcare", "energy"]
        score = optimizer.diversification_score(weights, categories)
        assert 0.0 <= score <= 1.0
        assert score > 0.8

        # Concentrated in one category → low diversification
        weights_concentrated = [0.7, 0.1, 0.1, 0.1]
        score_low = optimizer.diversification_score(weights_concentrated, categories)
        assert score_low < score

        # Single asset → zero diversification
        score_single = optimizer.diversification_score([1.0], ["tech"])
        assert score_single == 0.0

    def test_correlation_matrix(self):
        """Correlation matrix is calculated correctly."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()
        matrix = optimizer.correlation_matrix(assets)

        n = len(assets)
        assert len(matrix) == n
        for row in matrix:
            assert len(row) == n

        # Diagonal is 1.0
        for i in range(n):
            assert abs(matrix[i][i] - 1.0) < 1e-9

        # Symmetric
        for i in range(n):
            for j in range(n):
                assert abs(matrix[i][j] - matrix[j][i]) < 1e-9

        # Values in [-1, 1]
        for i in range(n):
            for j in range(n):
                assert -1.0 <= matrix[i][j] <= 1.0

    def test_efficient_frontier(self):
        """Efficient frontier is generated with requested points."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()
        points = 5
        frontier = optimizer.efficient_frontier(assets, points=points)

        assert isinstance(frontier, list)
        assert len(frontier) == points
        for p in frontier:
            assert isinstance(p, Portfolio)
            assert len(p.assets) > 0

        # Frontier should show increasing return with increasing risk
        returns = [p.expected_return for p in frontier]
        risks = [p.risk for p in frontier]
        assert returns == sorted(returns)
        assert risks == sorted(risks)

    def test_rebalancing(self):
        """Rebalancing recommendations are generated."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()

        current = Portfolio(
            assets=assets[:3],
            weights=[0.5, 0.3, 0.2],
            expected_return=0.09,
            risk=0.14,
            sharpe=0.64,
        )
        target = Portfolio(
            assets=assets,
            weights=[0.25, 0.25, 0.2, 0.15, 0.15],
            expected_return=0.088,
            risk=0.12,
            sharpe=0.73,
        )
        result = optimizer.rebalancing(current, target)

        assert isinstance(result, dict)
        assert "trades" in result
        assert "current_value" in result
        assert "target_value" in result
        assert "rebalancing_cost" in result
        assert isinstance(result["trades"], dict)
        # Should recommend some trades since portfolios differ
        assert len(result["trades"]) > 0

    def test_portfolio_report(self):
        """Portfolio report is generated with key metrics."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()
        portfolio = optimizer.optimize(assets, risk_tolerance=0.5, budget=300.0)
        report = optimizer.generate_portfolio_report(portfolio)

        assert isinstance(report, dict)
        assert "num_assets" in report
        assert "expected_return" in report
        assert "risk" in report
        assert "sharpe" in report
        assert "weights" in report
        assert "diversification_score" in report
        assert report["num_assets"] == len(portfolio.assets)
        assert report["expected_return"] == pytest.approx(portfolio.expected_return)

    def test_constraint_handling(self):
        """Constraints are applied to filter assets."""
        optimizer = PortfolioOptimizer()
        assets = _sample_assets()

        # Max risk constraint
        constraints = {"max_risk": 0.13}
        filtered = optimizer.apply_constraints(assets, constraints)
        assert len(filtered) < len(assets)
        for a in filtered:
            assert a.risk <= 0.13

        # Min return constraint
        constraints = {"min_return": 0.08}
        filtered = optimizer.apply_constraints(assets, constraints)
        for a in filtered:
            assert a.expected_return >= 0.08

        # Category constraint
        constraints = {"categories": ["tech", "finance"]}
        filtered = optimizer.apply_constraints(assets, constraints)
        for a in filtered:
            assert a.category in ("tech", "finance")

        # Max cost constraint
        constraints = {"max_cost": 100.0}
        filtered = optimizer.apply_constraints(assets, constraints)
        for a in filtered:
            assert a.cost <= 100.0

        # No constraints → all assets
        filtered = optimizer.apply_constraints(assets, {})
        assert len(filtered) == len(assets)

    def test_portfolio_stability(self):
        """Portfolio stability is scored based on correlations."""
        optimizer = PortfolioOptimizer()

        # Low correlations → high stability
        low_corr = [
            [1.0, 0.1, 0.1],
            [0.1, 1.0, 0.1],
            [0.1, 0.1, 1.0],
        ]
        weights = [1 / 3, 1 / 3, 1 / 3]
        stability = optimizer.portfolio_stability(weights, low_corr)
        assert 0.0 <= stability <= 1.0
        assert stability > 0.7

        # High correlations → low stability
        high_corr = [
            [1.0, 0.9, 0.9],
            [0.9, 1.0, 0.9],
            [0.9, 0.9, 1.0],
        ]
        stability_low = optimizer.portfolio_stability(weights, high_corr)
        assert stability_low < stability
