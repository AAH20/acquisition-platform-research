"""Tests for market analysis module."""

import pytest

from acquisition_platform.exceptions import EmptyInputError, ValidationError
from acquisition_platform.market_analysis import (
    CompetitiveProfile,
    MarketAnalysisResult,
    MarketAnalyzer,
    MarketData,
)


class TestMarketAnalyzer:
    """TDD tests for the market analysis module."""

    def test_tam_sam_som(self):
        """TAM/SAM/SOM calculated correctly."""
        analyzer = MarketAnalyzer()
        market = analyzer.calculate_tam_sam_som(
            name="Cloud Infrastructure",
            total_addressable=100_000_000_000,
            serviceable=40_000_000_000,
            obtainable=10_000_000_000,
        )
        assert market.name == "Cloud Infrastructure"
        assert market.tam == 100_000_000_000
        assert market.sam == 40_000_000_000
        assert market.som == 10_000_000_000
        assert market.growth_rate == 0.0
        assert market.year > 0

    def test_market_growth_rate(self):
        """CAGR calculated."""
        analyzer = MarketAnalyzer()
        rate = analyzer.growth_rate(start_value=100, end_value=200, years=5)
        expected = (200 / 100) ** (1 / 5) - 1
        assert rate == pytest.approx(expected, rel=1e-6)
        assert rate == pytest.approx(0.1487, rel=1e-3)

    def test_competitive_density(self):
        """Competitive density scored."""
        analyzer = MarketAnalyzer()
        competitors = [
            CompetitiveProfile(competitor="A", market_share=0.4),
            CompetitiveProfile(competitor="B", market_share=0.3),
            CompetitiveProfile(competitor="C", market_share=0.3),
        ]
        density = analyzer.competitive_density(competitors)
        assert 0.0 < density <= 1.0
        # With 3 competitors and moderate concentration
        assert density > 0.1

    def test_empty_market(self):
        """Empty market returns defaults."""
        analyzer = MarketAnalyzer()
        market = MarketData(name="Empty", tam=0, sam=0, som=0, growth_rate=0, year=2024)
        competitors = []
        assert analyzer.market_attractiveness(market, competitors) == 0.0
        assert analyzer.competitive_density(competitors) == 0.0
        report = analyzer.generate_market_report(market, competitors)
        assert report.attractiveness == 0.0
        assert report.density == 0.0
        assert isinstance(report.forecast, list)

    def test_market_attractiveness(self):
        """Attractiveness score calculated."""
        analyzer = MarketAnalyzer()
        market = MarketData(
            name="SaaS",
            tam=5_000_000_000,
            sam=2_000_000_000,
            som=500_000_000,
            growth_rate=0.10,
            year=2024,
        )
        competitors = [
            CompetitiveProfile(competitor="A", market_share=0.4),
            CompetitiveProfile(competitor="B", market_share=0.3),
            CompetitiveProfile(competitor="C", market_share=0.3),
        ]
        score = analyzer.market_attractiveness(market, competitors)
        assert 0.0 <= score <= 1.0
        assert score > 0.5

    def test_market_sizing(self):
        """Bottom-up sizing applied."""
        analyzer = MarketAnalyzer()
        segments = [100_000, 200_000, 300_000, 400_000]
        total = analyzer.bottom_up_sizing(segments)
        assert total == 1_000_000

    def test_competitive_analysis(self):
        """Competitor analysis scored."""
        analyzer = MarketAnalyzer()
        competitors = [
            CompetitiveProfile(
                competitor="Alpha", market_share=0.5, strength="brand", weakness="price"
            ),
            CompetitiveProfile(
                competitor="Beta", market_share=0.3, strength="tech", weakness="scale"
            ),
            CompetitiveProfile(
                competitor="Gamma", market_share=0.2, strength="service", weakness="reach"
            ),
        ]
        analysis = analyzer.competitive_analysis(competitors)
        assert analysis["count"] == 3
        assert analysis["total_share"] == pytest.approx(1.0)
        assert analysis["leader"] == "Alpha"
        assert analysis["hhi"] > 0
        assert analysis["density"] > 0

    def test_market_report(self):
        """Report generated."""
        analyzer = MarketAnalyzer()
        market = MarketData(
            name="FinTech",
            tam=10_000_000_000,
            sam=4_000_000_000,
            som=1_000_000_000,
            growth_rate=0.15,
            year=2024,
        )
        competitors = [
            CompetitiveProfile(competitor="A", market_share=0.35),
            CompetitiveProfile(competitor="B", market_share=0.25),
            CompetitiveProfile(competitor="C", market_share=0.20),
            CompetitiveProfile(competitor="D", market_share=0.15),
            CompetitiveProfile(competitor="E", market_share=0.05),
        ]
        report = analyzer.generate_market_report(market, competitors)
        assert isinstance(report, MarketAnalysisResult)
        assert report.market.name == "FinTech"
        assert 0.0 <= report.attractiveness <= 1.0
        assert 0.0 <= report.density <= 1.0
        assert len(report.entry_barriers) > 0
        assert len(report.forecast) == 5

    def test_market_forecast(self):
        """Forecast generated."""
        analyzer = MarketAnalyzer()
        market = MarketData(
            name="AI",
            tam=1000,
            sam=500,
            som=100,
            growth_rate=0.10,
            year=2024,
        )
        forecast = analyzer.market_forecast(market, years=3)
        assert len(forecast) == 3
        assert forecast[0] == pytest.approx(1100.0)
        assert forecast[1] == pytest.approx(1210.0)
        assert forecast[2] == pytest.approx(1331.0)

    def test_market_entry_barriers(self):
        """Entry barriers assessed."""
        analyzer = MarketAnalyzer()
        market = MarketData(
            name="Enterprise Software",
            tam=50_000_000_000,
            sam=20_000_000_000,
            som=2_000_000_000,
            growth_rate=0.08,
            year=2024,
        )
        competitors = [
            CompetitiveProfile(competitor=f"C{i}", market_share=0.1) for i in range(6)
        ]
        barriers = analyzer.entry_barriers(market, competitors)
        assert isinstance(barriers, list)
        assert len(barriers) > 0
        assert "high_capital_requirements" in barriers
        assert "established_competitors" in barriers
