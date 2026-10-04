"""Dynamic pricing engine based on Stackelberg game theory.

The Stackelberg competition model, where a leader firm sets its price first
and follower firms respond, is known to be Sigma_2^p-complete in its general
form. This module implements a tractable approximation suitable for M&A
target valuation and acquisition pricing scenarios.
"""

from dataclasses import dataclass

from acquisition_platform.exceptions import InvalidRangeError, ValidationError
from acquisition_platform.serialization import SerializableMixin


@dataclass
class PriceRecommendation(SerializableMixin):
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
        if base_value <= 0:
            raise ValidationError(f"base_value must be positive, got {base_value}")
        if demand_level < 0 or demand_level > 1:
            raise InvalidRangeError(
                f"demand_level must be in [0, 1], got {demand_level}"
            )
        if competition_level < 0 or competition_level > 1:
            raise InvalidRangeError(
                f"competition_level must be in [0, 1], got {competition_level}"
            )

        valid_conditions = {"bull", "bear", "normal"}
        if market_condition not in valid_conditions:
            raise ValidationError(
                f"market_condition must be one of {valid_conditions}, got '{market_condition}'"
            )

        if base_value <= 0:
            raise ValidationError(f"base_value must be positive, got {base_value}")

        demand_multiplier = 0.8 + demand_level * 0.4
        competition_multiplier = 1.2 - competition_level * 0.4

        market_multipliers = {
            "bull": 1.15,
            "bear": 0.85,
            "normal": 1.0,
        }
        market_multiplier = market_multipliers.get(market_condition, 1.0)

        raw_price = (
            base_value * demand_multiplier * competition_multiplier * market_multiplier
        )
        floor_price = base_value * 0.7
        ceiling_price = base_value * 1.5
        recommended_price = max(floor_price, min(ceiling_price, raw_price))
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
