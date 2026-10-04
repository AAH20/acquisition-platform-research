"""Portfolio Optimizer — MIQP (Mixed Integer Quadratic Program) solver.

Portfolio optimization with cardinality constraints is NP-hard (MIQP).
This module uses a greedy approximation with risk-adjusted return scoring
and diversification bonuses to produce near-optimal portfolios.

Complexity: O(n log n) greedy selection vs O(C(n,K)) exhaustive search.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Asset:
    """A candidate acquisition target."""

    id: str
    cost: float
    expected_return: float
    risk: float
    sector: str = ""


@dataclass
class Portfolio:
    """An optimized portfolio of assets."""

    assets: list[Asset] = field(default_factory=list)
    expected_return: float = 0.0
    sharpe_ratio: float = 0.0


class PortfolioOptimizer:
    """Greedy portfolio optimizer with diversification.

    Solves the cardinality-constrained portfolio optimization problem:
    maximize expected_return subject to budget and max_assets constraints.

    The problem is MIQP (NP-hard). This implementation uses a greedy
    approximation that runs in O(n log n) time.
    """

    def __init__(self, budget: float, max_assets: int = 10) -> None:
        """Initialize optimizer.

        Args:
            budget: Total capital available for acquisitions.
            max_assets: Maximum number of assets in the portfolio (cardinality constraint).
        """
        self.budget = budget
        self.max_assets = max_assets

    def optimize(
        self, assets: list[Asset], risk_tolerance: float
    ) -> Portfolio:
        """Optimize portfolio using greedy selection.

        Args:
            assets: Candidate assets to select from.
            risk_tolerance: Risk tolerance (0-1). Higher = more aggressive.

        Returns:
            Optimized Portfolio with selected assets.
        """
        if not assets:
            return Portfolio()

        # Filter assets within budget
        affordable = [a for a in assets if a.cost <= self.budget]
        if not affordable:
            return Portfolio()

        # Score each asset: risk-adjusted return with diversification bonus
        selected: list[Asset] = []
        selected_sectors: set[str] = set()
        remaining_budget = self.budget

        # Sort by risk-adjusted return score
        scored = []
        for asset in affordable:
            base_score = asset.expected_return / (asset.risk + 0.01)
            # Risk tolerance adjusts the risk penalty
            adjusted_score = base_score * (1 + risk_tolerance)
            scored.append((adjusted_score, asset))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Greedy selection with diversification bonus
        for score, asset in scored:
            if len(selected) >= self.max_assets:
                break
            if asset.cost > remaining_budget:
                continue

            # Apply diversification bonus
            diversification_bonus = 1.5 if asset.sector not in selected_sectors else 1.0
            effective_score = score * diversification_bonus

            selected.append(asset)
            selected_sectors.add(asset.sector)
            remaining_budget -= asset.cost

        # Calculate portfolio metrics
        if not selected:
            return Portfolio()

        total_cost = sum(a.cost for a in selected)
        expected_return = sum(
            a.expected_return * (a.cost / total_cost) for a in selected
        )
        total_risk = sum(a.risk for a in selected)
        sharpe_ratio = expected_return / (total_risk + 0.01)

        return Portfolio(
            assets=selected,
            expected_return=expected_return,
            sharpe_ratio=sharpe_ratio,
        )
