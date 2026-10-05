"""Tests for competitive intelligence module."""
import pytest
from acquisition_platform.competitive_intel import (
    CompetitorProfile,
    CompetitiveSignal,
    CompetitiveIntelResult,
    CompetitiveIntelAnalyzer,
)


class TestCompetitiveIntel:
    """TDD tests for the competitive intelligence module."""

    def test_competitor_profiling(self):
        """Competitor profiled correctly."""
        analyzer = CompetitiveIntelAnalyzer()
        profile = analyzer.profile_competitor(
            name="Acme Corp",
            market_share=25.0,
            strengths=["brand", "distribution"],
            weaknesses=["high costs"],
            strategy="cost leadership",
        )
        assert isinstance(profile, CompetitorProfile)
        assert profile.name == "Acme Corp"
        assert profile.market_share == 25.0
        assert profile.strengths == ["brand", "distribution"]
        assert profile.weaknesses == ["high costs"]
        assert profile.strategy == "cost leadership"

    def test_market_share_analysis(self):
        """Market share analyzed."""
        analyzer = CompetitiveIntelAnalyzer()
        competitors = [
            analyzer.profile_competitor("A", 40.0, [], [], ""),
            analyzer.profile_competitor("B", 30.0, [], [], ""),
            analyzer.profile_competitor("C", 20.0, [], [], ""),
        ]
        result = analyzer.market_share_analysis(competitors)
        assert isinstance(result, dict)
        assert result["total_share"] == pytest.approx(90.0)
        assert result["average_share"] == pytest.approx(30.0)
        assert result["leader"] == "A"
        assert result["leader_share"] == pytest.approx(40.0)
        assert result["competitor_count"] == 3

    def test_competitive_positioning(self):
        """Positioning scored."""
        analyzer = CompetitiveIntelAnalyzer()
        competitors = [
            analyzer.profile_competitor("A", 40.0, ["brand"], ["cost"], ""),
            analyzer.profile_competitor("B", 30.0, [], [], ""),
        ]
        score = analyzer.competitive_positioning(competitors, "A")
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_empty_intel(self):
        """Empty intel returns defaults."""
        analyzer = CompetitiveIntelAnalyzer()
        result = analyzer.generate_competitive_report([], [])
        assert isinstance(result, CompetitiveIntelResult)
        assert result.competitors == []
        assert result.signals == []
        assert result.positioning_score == 0.0
        assert result.alerts == []

    def test_war_gaming(self):
        """War game scenario scored."""
        analyzer = CompetitiveIntelAnalyzer()
        competitors = [
            analyzer.profile_competitor("A", 40.0, ["brand"], ["cost"], ""),
            analyzer.profile_competitor("B", 35.0, ["tech"], [], ""),
        ]
        score = analyzer.war_game_scenario(competitors, "price_war")
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_competitive_response(self):
        """Response predicted."""
        analyzer = CompetitiveIntelAnalyzer()
        competitor = analyzer.profile_competitor(
            "A", 40.0, ["brand"], ["high costs"], "cost leadership"
        )
        response = analyzer.predict_competitive_response(competitor, "price_cut")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_signals_tracking(self):
        """Signals tracked."""
        analyzer = CompetitiveIntelAnalyzer()
        signal = analyzer.track_signal(
            signal_type="pricing",
            source="market_scan",
            timestamp="2024-01-15T10:00:00Z",
            impact=0.75,
        )
        assert isinstance(signal, CompetitiveSignal)
        assert signal.signal_type == "pricing"
        assert signal.source == "market_scan"
        assert signal.timestamp == "2024-01-15T10:00:00Z"
        assert signal.impact == pytest.approx(0.75)

    def test_competitive_report(self):
        """Report generated."""
        analyzer = CompetitiveIntelAnalyzer()
        competitors = [
            analyzer.profile_competitor("A", 40.0, ["brand"], ["cost"], ""),
            analyzer.profile_competitor("B", 30.0, ["tech"], [], ""),
        ]
        signals = [
            analyzer.track_signal("pricing", "scan", "2024-01-15T10:00:00Z", 0.8),
            analyzer.track_signal("product_launch", "news", "2024-01-16T10:00:00Z", 0.6),
        ]
        report = analyzer.generate_competitive_report(competitors, signals)
        assert isinstance(report, CompetitiveIntelResult)
        assert len(report.competitors) == 2
        assert len(report.signals) == 2
        assert isinstance(report.positioning_score, float)
        assert isinstance(report.alerts, list)

    def test_roci_calculation(self):
        """Return on CI calculated."""
        analyzer = CompetitiveIntelAnalyzer()
        roci = analyzer.roci_calculation(investment=100.0, value_generated=150.0)
        assert isinstance(roci, float)
        assert roci == pytest.approx(0.5)
        # Edge case: zero investment
        with pytest.raises(Exception):
            analyzer.roci_calculation(investment=0.0, value_generated=100.0)

    def test_competitive_alert(self):
        """Alert generated."""
        analyzer = CompetitiveIntelAnalyzer()
        signals = [
            analyzer.track_signal("pricing", "scan", "2024-01-15T10:00:00Z", 0.9),
            analyzer.track_signal("product_launch", "news", "2024-01-16T10:00:00Z", 0.3),
        ]
        alerts = analyzer.generate_competitive_alert(threshold=0.7, signals=signals)
        assert isinstance(alerts, list)
        assert len(alerts) == 1
        assert "pricing" in alerts[0].lower() or "0.9" in alerts[0]
