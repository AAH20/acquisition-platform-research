"""Portfolio Optimization Module (Wave 2).

Modern portfolio theory implementation with mean-variance optimization,
diversification scoring, efficient frontier generation, and rebalancing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Asset:
    """A financial asset with return/risk characteristics."""

    name: str
    expected_return: float
    risk: float
    cost: float
    category: str


@dataclass
class Portfolio:
    """A portfolio of assets with weights and computed metrics."""

    assets: list[Asset] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    expected_return: float = 0.0
    risk: float = 0.0
    sharpe: float = 0.0


class PortfolioOptimizer:
    """Mean-variance portfolio optimizer.

    Implements Markowitz-style optimization with diversification bonuses,
    constraint handling, and efficient frontier generation.
    """

    def optimize(
        self,
        assets: list[Asset],
        risk_tolerance: float,
        budget: float,
    ) -> Portfolio:
        """Optimize portfolio weights for given assets and constraints.

        Uses a greedy risk-adjusted selection strategy: assets are scored by
        return-to-risk ratio adjusted for risk tolerance, then selected within
        budget. Weights are assigned proportional to risk-adjusted scores.

        Args:
            assets: Candidate assets to include.
            risk_tolerance: 0 (conservative) to 1 (aggressive).
            budget: Maximum total cost of selected assets.

        Returns:
            Optimized Portfolio with weights summing to 1.0.
        """
        if not assets:
            return Portfolio()

        # Filter affordable assets
        affordable = [a for a in assets if a.cost <= budget]
        if not affordable:
            return Portfolio()

        # Score assets: risk-adjusted return scaled by risk tolerance
        scored: list[tuple[float, Asset]] = []
        for asset in affordable:
            base_score = asset.expected_return / (asset.risk + 0.01)
            # Higher risk tolerance → less penalty for risk
            adjusted_score = base_score * (1.0 + risk_tolerance)
            scored.append((adjusted_score, asset))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Greedy selection within budget
        selected: list[Asset] = []
        selected_scores: list[float] = []
        remaining = budget
        for score, asset in scored:
            if asset.cost <= remaining:
                selected.append(asset)
                selected_scores.append(score)
                remaining -= asset.cost

        if not selected:
            return Portfolio()

        # Weights proportional to risk-adjusted scores
        total_score = sum(selected_scores)
        weights = [s / total_score for s in selected_scores]

        # Portfolio metrics
        expected_return = sum(w * a.expected_return for w, a in zip(weights, selected))
        # Risk: weighted average with diversification benefit
        avg_risk = sum(w * a.risk for w, a in zip(weights, selected))
        # Diversification reduces effective risk
        categories = set(a.category for a in selected)
        diversification_factor = 1.0 - 0.05 * (len(categories) - 1)
        diversification_factor = max(0.7, diversification_factor)
        risk = avg_risk * diversification_factor
        sharpe = expected_return / (risk + 0.001)

        return Portfolio(
            assets=selected,
            weights=weights,
            expected_return=expected_return,
            risk=risk,
            sharpe=sharpe,
        )

    def risk_return_tradeoff(self, assets: list[Asset]) -> dict[str, dict[str, float]]:
        """Calculate risk-return tradeoff metrics for each asset.

        Args:
            assets: Assets to analyze.

        Returns:
            Dict mapping asset name to its tradeoff metrics.
        """
        result: dict[str, dict[str, float]] = {}
        for asset in assets:
            ratio = asset.expected_return / (asset.risk + 0.001)
            result[asset.name] = {
                "return_risk_ratio": ratio,
                "expected_return": asset.expected_return,
                "risk": asset.risk,
            }
        return result

    def diversification_score(self, weights: list[float], categories: list[str]) -> float:
        """Compute diversification score using effective number of categories.

        Uses the Herfindahl-Hirschman Index (HHI) over category weights.
        Score = (1 - HHI) / (1 - 1/n) where n = number of distinct categories.
        Returns 0.0 for single-category portfolios, 1.0 for perfect diversification.

        Args:
            weights: Portfolio weights.
            categories: Category for each corresponding weight.

        Returns:
            Diversification score in [0, 1].
        """
        if len(weights) == 0 or len(categories) == 0:
            return 0.0

        # Aggregate weights by category
        category_weights: dict[str, float] = {}
        for w, cat in zip(weights, categories):
            category_weights[cat] = category_weights.get(cat, 0.0) + w

        n = len(category_weights)
        if n <= 1:
            return 0.0

        # HHI = sum of squared category weights
        hhi = sum(w * w for w in category_weights.values())

        # Normalize: 0 = fully concentrated, 1 = perfectly diversified
        score = (1.0 - hhi) / (1.0 - 1.0 / n)
        return max(0.0, min(1.0, score))

    def correlation_matrix(self, assets: list[Asset]) -> list[list[float]]:
        """Generate a correlation matrix for the given assets.

        Uses category-based heuristic: same-category assets have higher
        correlation (0.6), different categories have lower (0.15).
        Adds small deterministic variation based on asset properties.

        Args:
            assets: Assets to correlate.

        Returns:
            NxN symmetric correlation matrix with 1.0 on diagonal.
        """
        n = len(assets)
        matrix: list[list[float]] = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                elif i < j:
                    if assets[i].category == assets[j].category:
                        base_corr = 0.6
                    else:
                        base_corr = 0.15
                    # Small deterministic variation
                    variation = 0.05 * math.sin(i * 3.7 + j * 1.3)
                    corr = base_corr + variation
                    corr = max(-1.0, min(1.0, corr))
                    matrix[i][j] = corr
                    matrix[j][i] = corr

        return matrix

    def efficient_frontier(self, assets: list[Asset], points: int) -> list[Portfolio]:
        """Generate the efficient frontier by varying risk tolerance.

        Optimizes portfolios at evenly-spaced risk tolerances from 0 to 1,
        then sorts by expected return (and risk).

        Args:
            assets: Candidate assets.
            points: Number of frontier points to generate.

        Returns:
            List of Portfolio objects along the efficient frontier.
        """
        if points <= 0 or not assets:
            return []

        frontier: list[Portfolio] = []
        for i in range(points):
            risk_tol = i / (points - 1) if points > 1 else 0.5
            portfolio = self.optimize(assets, risk_tolerance=risk_tol, budget=float("inf"))
            if portfolio.assets:
                frontier.append(portfolio)

        # Sort by expected return (ascending) — frontier property
        frontier.sort(key=lambda p: (p.expected_return, p.risk))
        return frontier

    def rebalancing(self, current: Portfolio, target: Portfolio) -> dict[str, Any]:
        """Generate rebalancing recommendations between two portfolios.

        Compares current and target weights per asset, computes trades needed
        to transition, and estimates rebalancing cost.

        Args:
            current: Current portfolio state.
            target: Desired target portfolio.

        Returns:
            Dict with trades, current_value, target_value, rebalancing_cost.
        """
        # Build weight maps
        current_weights: dict[str, float] = {
            a.name: w for a, w in zip(current.assets, current.weights)
        }
        target_weights: dict[str, float] = {
            a.name: w for a, w in zip(target.assets, target.weights)
        }

        all_names = set(current_weights) | set(target_weights)
        trades: dict[str, float] = {}
        total_abs_change = 0.0

        for name in all_names:
            curr_w = current_weights.get(name, 0.0)
            targ_w = target_weights.get(name, 0.0)
            diff = targ_w - curr_w
            if abs(diff) > 1e-9:
                trades[name] = diff
                total_abs_change += abs(diff)

        current_value = sum(a.cost for a in current.assets)
        target_value = sum(a.cost for a in target.assets)
        # Cost: 0.5% of absolute weight change * average value
        avg_value = (current_value + target_value) / 2.0
        rebalancing_cost = 0.005 * total_abs_change * avg_value

        return {
            "trades": trades,
            "current_value": current_value,
            "target_value": target_value,
            "rebalancing_cost": rebalancing_cost,
        }

    def apply_constraints(
        self,
        assets: list[Asset],
        constraints: dict[str, Any],
    ) -> list[Asset]:
        """Filter assets based on constraints.

        Supported constraints:
            - max_risk: Maximum allowed risk per asset.
            - min_return: Minimum expected return per asset.
            - max_cost: Maximum cost per asset.
            - categories: List of allowed categories.

        Args:
            assets: Assets to filter.
            constraints: Dict of constraint parameters.

        Returns:
            Filtered list of assets satisfying all constraints.
        """
        result = assets

        if "max_risk" in constraints:
            result = [a for a in result if a.risk <= constraints["max_risk"]]
        if "min_return" in constraints:
            result = [a for a in result if a.expected_return >= constraints["min_return"]]
        if "max_cost" in constraints:
            result = [a for a in result if a.cost <= constraints["max_cost"]]
        if "categories" in constraints:
            allowed = set(constraints["categories"])
            result = [a for a in result if a.category in allowed]

        return result

    def portfolio_stability(self, weights: list[float], correlations: list[list[float]]) -> float:
        """Compute portfolio stability score based on weighted correlations.

        Stability = 1 - (weighted average pairwise correlation).
        Lower correlations → higher stability.

        Args:
            weights: Portfolio weights.
            correlations: NxN correlation matrix.

        Returns:
            Stability score in [0, 1].
        """
        n = len(weights)
        if n == 0:
            return 0.0
        if n == 1:
            return 1.0

        # Weighted average of off-diagonal correlations
        weighted_corr_sum = 0.0
        weight_sum = 0.0
        for i in range(n):
            for j in range(n):
                if i != j:
                    weighted_corr_sum += weights[i] * weights[j] * correlations[i][j]
                    weight_sum += weights[i] * weights[j]

        if weight_sum == 0.0:
            return 1.0

        avg_correlation = weighted_corr_sum / weight_sum
        stability = 1.0 - avg_correlation
        return max(0.0, min(1.0, stability))

    def generate_portfolio_report(self, portfolio: Portfolio) -> dict[str, Any]:
        """Generate a comprehensive portfolio report.

        Args:
            portfolio: Portfolio to report on.

        Returns:
            Dict with key portfolio metrics and metadata.
        """
        categories = [a.category for a in portfolio.assets]
        div_score = self.diversification_score(portfolio.weights, categories)

        return {
            "num_assets": len(portfolio.assets),
            "expected_return": portfolio.expected_return,
            "risk": portfolio.risk,
            "sharpe": portfolio.sharpe,
            "weights": {
                a.name: w for a, w in zip(portfolio.assets, portfolio.weights)
            },
            "diversification_score": div_score,
            "total_cost": sum(a.cost for a in portfolio.assets),
        }
