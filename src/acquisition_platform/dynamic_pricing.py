"""Dynamic pricing engine based on Stackelberg game theory.

The Stackelberg competition model, where a leader firm sets its price first
and follower firms respond, is known to be Sigma_2^p-complete in its general
form. This module implements a tractable approximation suitable for M&A
target valuation and acquisition pricing scenarios.
"""

from dataclasses import dataclass


@dataclass
class PriceRecommendation:
    """Result of a dynamic pricing calculation."""

    recommended_price: float
    confidence: float
    floor_price: float
    ceiling_price: float
    equilibrium_price: float


class PricingEngine:
    """Dynamic pricing engine using Stackelberg-inspired multipliers."""

    def recommend_price(
        self,
        base_value: float,
        demand_level: float,
        competition_level: float,
        market_condition: str,
    ) -> PriceRecommendation:
        """Compute a price recommendation given market conditions.

        Args:
            base_value: The intrinsic/base valuation of the target.
            demand_level: Normalized demand in [0, 1].
            competition_level: Normalized competition intensity in [0, 1].
            market_condition: One of "bull", "bear", or "normal".

        Returns:
            A PriceRecommendation with computed pricing metrics.
        """
        demand_multiplier = 0.8 + demand_level * 0.4
        competition_multiplier = 1.2 - competition_level * 0.4

        market_multipliers = {
            "bull": 1.15,
            "bear": 0.85,
            "normal": 1.0,
        }
        market_multiplier = market_multipliers.get(market_condition, 1.0)

        recommended_price = (
            base_value * demand_multiplier * competition_multiplier * market_multiplier
        )
        floor_price = base_value * 0.7
        ceiling_price = base_value * 1.5
        equilibrium_price = (
            base_value * (demand_multiplier + competition_multiplier) / 2
        )
        confidence = 1 - abs(demand_level - competition_level)

        return PriceRecommendation(
            recommended_price=recommended_price,
            confidence=confidence,
            floor_price=floor_price,
            ceiling_price=ceiling_price,
            equilibrium_price=equilibrium_price,
        )
