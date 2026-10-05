"""Market analysis module for acquisition target evaluation.

This module provides tools for market sizing (TAM/SAM/SOM), growth rate
calculation, competitive density analysis, market attractiveness scoring,
and entry barrier assessment. These metrics are essential for evaluating
the strategic value of potential acquisition targets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin


@dataclass
class MarketData:
    """Market sizing data for a specific market.

    Attributes:
        name: Market name or identifier.
        tam: Total Addressable Market value.
        sam: Serviceable Addressable Market value.
        som: Serviceable Obtainable Market value.
        growth_rate: Annual market growth rate (CAGR).
        year: Year the data pertains to.
    """

    name: str
    tam: float
    sam: float
    som: float
    growth_rate: float
    year: int = field(default_factory=lambda: datetime.now().year)


@dataclass
class CompetitiveProfile:
    """Profile of a single competitor in the market.

    Attributes:
        competitor: Competitor name.
        market_share: Competitor's market share (0-1).
        strength: Key strength of the competitor.
        weakness: Key weakness of the competitor.
    """

    competitor: str
    market_share: float
    strength: str = ""
    weakness: str = ""


@dataclass
class MarketAnalysisResult(SerializableMixin):
    """Comprehensive market analysis result.

    Attributes:
        market: The market data analyzed.
        attractiveness: Overall attractiveness score (0-1).
        density: Competitive density score (0-1).
        entry_barriers: List of identified entry barriers.
        forecast: Projected market size for upcoming years.
    """

    market: MarketData
    attractiveness: float
    density: float
    entry_barriers: list[str]
    forecast: list[float]


class MarketAnalyzer:
    """Analyzer for market sizing, competition, and attractiveness."""

    def calculate_tam_sam_som(
        self,
        name: str,
        total_addressable: float,
        serviceable: float,
        obtainable: float,
    ) -> MarketData:
        """Calculate TAM/SAM/SOM market sizing.

        Args:
            name: Market name.
            total_addressable: Total addressable market value.
            serviceable: Serviceable addressable market value.
            obtainable: Serviceable obtainable market value.

        Returns:
            MarketData with the provided sizing values.

        Raises:
            ValidationError: If any value is negative or if the hierarchy
                TAM >= SAM >= SOM is violated.
        """
        if total_addressable < 0:
            raise ValidationError(
                f"total_addressable must be non-negative, got {total_addressable}"
            )
        if serviceable < 0:
            raise ValidationError(
                f"serviceable must be non-negative, got {serviceable}"
            )
        if obtainable < 0:
            raise ValidationError(
                f"obtainable must be non-negative, got {obtainable}"
            )
        if serviceable > total_addressable:
            raise ValidationError(
                f"serviceable ({serviceable}) cannot exceed "
                f"total_addressable ({total_addressable})"
            )
        if obtainable > serviceable:
            raise ValidationError(
                f"obtainable ({obtainable}) cannot exceed "
                f"serviceable ({serviceable})"
            )
        return MarketData(
            name=name,
            tam=total_addressable,
            sam=serviceable,
            som=obtainable,
            growth_rate=0.0,
        )

    def growth_rate(self, start_value: float, end_value: float, years: int) -> float:
        """Calculate Compound Annual Growth Rate (CAGR).

        Args:
            start_value: Initial value.
            end_value: Final value.
            years: Number of years between measurements.

        Returns:
            CAGR as a decimal (e.g., 0.10 for 10% annual growth).

        Raises:
            ValidationError: If start_value or years is not positive.
        """
        if start_value <= 0:
            raise ValidationError(
                f"start_value must be positive, got {start_value}"
            )
        if years <= 0:
            raise ValidationError(f"years must be positive, got {years}")
        return float((end_value / start_value) ** (1.0 / years) - 1.0)

    def competitive_density(self, competitors: list[CompetitiveProfile]) -> float:
        """Calculate competitive density score.

        Combines the number of competitors with market share concentration
        (HHI) to produce a density score. Higher values indicate a more
        crowded, competitive market.

        Args:
            competitors: List of competitor profiles.

        Returns:
            Density score in [0, 1]. Returns 0.0 for empty input.
        """
        if not competitors:
            return 0.0
        n = len(competitors)
        hhi = sum(float(c.market_share) ** 2 for c in competitors)
        count_factor = min(1.0, n / 10.0)
        concentration_factor = 1.0 - hhi
        return float(count_factor * concentration_factor)

    def market_attractiveness(
        self, market: MarketData, competitors: list[CompetitiveProfile]
    ) -> float:
        """Calculate overall market attractiveness score.

        Combines market size, growth rate, and competitive landscape into
        a single attractiveness score.

        Args:
            market: Market data.
            competitors: List of competitor profiles.

        Returns:
            Attractiveness score in [0, 1]. Returns 0.0 for empty markets.
        """
        if market.tam <= 0:
            return 0.0
        size_score = min(1.0, math.log10(market.tam) / 12.0)
        growth_score = min(1.0, market.growth_rate / 0.20)
        density = self.competitive_density(competitors)
        competition_score = 1.0 - density
        attractiveness = (
            0.4 * size_score + 0.3 * growth_score + 0.3 * competition_score
        )
        return max(0.0, min(1.0, attractiveness))

    def bottom_up_sizing(self, segments: list[float]) -> float:
        """Calculate total market size using bottom-up approach.

        Sums individual segment sizes to arrive at a total market estimate.

        Args:
            segments: List of segment sizes.

        Returns:
            Total market size (sum of all segments).

        Raises:
            ValidationError: If any segment is negative.
        """
        for i, seg in enumerate(segments):
            if seg < 0:
                raise ValidationError(
                    f"segment[{i}] must be non-negative, got {seg}"
                )
        return sum(segments)

    def competitive_analysis(
        self, competitors: list[CompetitiveProfile]
    ) -> dict[str, Any]:
        """Perform comprehensive competitive analysis.

        Args:
            competitors: List of competitor profiles.

        Returns:
            Dictionary with count, total_share, leader, hhi, and density.
        """
        if not competitors:
            return {
                "count": 0,
                "total_share": 0.0,
                "leader": "",
                "hhi": 0.0,
                "density": 0.0,
            }
        total_share = sum(c.market_share for c in competitors)
        leader = max(competitors, key=lambda c: c.market_share).competitor
        hhi = sum(c.market_share**2 for c in competitors)
        density = self.competitive_density(competitors)
        return {
            "count": len(competitors),
            "total_share": total_share,
            "leader": leader,
            "hhi": hhi,
            "density": density,
        }

    def market_forecast(self, market: MarketData, years: int) -> list[float]:
        """Generate market size forecast.

        Projects market size forward using the current growth rate.

        Args:
            market: Market data with TAM and growth rate.
            years: Number of years to forecast.

        Returns:
            List of projected market sizes for each year.

        Raises:
            ValidationError: If years is not positive.
        """
        if years <= 0:
            raise ValidationError(f"years must be positive, got {years}")
        return [
            market.tam * (1.0 + market.growth_rate) ** (i + 1)
            for i in range(years)
        ]

    def entry_barriers(
        self, market: MarketData, competitors: list[CompetitiveProfile]
    ) -> list[str]:
        """Assess market entry barriers.

        Identifies potential barriers to entry based on market size,
        growth rate, competitive landscape, and obtainable market share.

        Args:
            market: Market data.
            competitors: List of competitor profiles.

        Returns:
            List of identified entry barrier identifiers.
        """
        barriers: list[str] = []
        if market.tam > 10_000_000_000:
            barriers.append("high_capital_requirements")
        if len(competitors) >= 5:
            barriers.append("established_competitors")
        if market.growth_rate < 0.05:
            barriers.append("slow_market_growth")
        density = self.competitive_density(competitors)
        if density > 0.7:
            barriers.append("intense_competition")
        if market.tam > 0 and market.som / market.tam < 0.01:
            barriers.append("low_obtainable_share")
        return barriers

    def generate_market_report(
        self, market: MarketData, competitors: list[CompetitiveProfile]
    ) -> MarketAnalysisResult:
        """Generate comprehensive market analysis report.

        Combines all analysis methods into a single result object.

        Args:
            market: Market data.
            competitors: List of competitor profiles.

        Returns:
            MarketAnalysisResult with all computed metrics.
        """
        attractiveness = self.market_attractiveness(market, competitors)
        density = self.competitive_density(competitors)
        barriers = self.entry_barriers(market, competitors)
        forecast = self.market_forecast(market, years=5)
        return MarketAnalysisResult(
            market=market,
            attractiveness=attractiveness,
            density=density,
            entry_barriers=barriers,
            forecast=forecast,
        )
