"""Tests for Sovereign Wealth Fund matching module."""
import pytest

from acquisition_platform.swf_matching import (
    SWFProfile,
    Opportunity,
    SWFMatch,
    SWFMatcher,
)


class TestSWFProfileCreation:
    """TDD tests for SWF profile creation."""

    def test_swf_profile_creation(self):
        """SWF profile created with all required fields."""
        matcher = SWFMatcher()
        profile = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US", "EU"],
            sector_focus=["tech", "energy"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        assert profile.name == "Test Fund"
        assert profile.aum == 1000000.0
        assert profile.horizon_years == 10
        assert profile.risk_tolerance == 0.5
        assert profile.geographic_focus == ["US", "EU"]
        assert profile.sector_focus == ["tech", "energy"]
        assert profile.min_deal_size == 100000.0
        assert profile.max_deal_size == 5000000.0


class TestSWFMatching:
    """TDD tests for SWF matching to opportunities."""

    def test_swf_matching(self):
        """SWF matched to opportunities produces SWFMatch objects."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp = Opportunity(
            name="Tech Acquisition",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        match = matcher.match(swf, opp)
        assert isinstance(match, SWFMatch)
        assert match.swf == swf
        assert match.opportunity == opp
        assert 0.0 <= match.score <= 1.0
        assert match.fit_level in ("high", "medium", "low")


class TestSWFCriteriaScoring:
    """TDD tests for investment criteria scoring."""

    def test_swf_criteria_scoring(self):
        """Investment criteria scored between 0 and 1."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp = Opportunity(
            name="Tech Acquisition",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        score = matcher.criteria_score(swf, opp)
        assert 0.0 <= score <= 1.0


class TestEmptyMatches:
    """TDD tests for empty matches handling."""

    def test_empty_matches(self):
        """Empty matches returns empty list."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        matches = matcher.match(swf, [])
        assert matches == []


class TestPortfolioFit:
    """TDD tests for portfolio fit assessment."""

    def test_portfolio_fit(self):
        """Portfolio fit assessed as a float between 0 and 1."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opps = [
            Opportunity(
                name="Tech Acquisition",
                sector="tech",
                geography="US",
                deal_size=500000.0,
                expected_return=0.15,
                risk_score=0.4,
                trl=7,
            ),
            Opportunity(
                name="Energy Deal",
                sector="energy",
                geography="US",
                deal_size=300000.0,
                expected_return=0.12,
                risk_score=0.3,
                trl=6,
            ),
        ]
        fit = matcher.portfolio_fit(swf, opps)
        assert 0.0 <= fit <= 1.0


class TestGeographicPreference:
    """TDD tests for geographic preference."""

    def test_geographic_preference(self):
        """Geographic preference applied correctly."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US", "EU"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp_match = Opportunity(
            name="US Deal",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        opp_no_match = Opportunity(
            name="Asia Deal",
            sector="tech",
            geography="Asia",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        score_match = matcher.geographic_preference(swf, opp_match)
        score_no_match = matcher.geographic_preference(swf, opp_no_match)
        assert score_match > score_no_match
        assert 0.0 <= score_match <= 1.0
        assert 0.0 <= score_no_match <= 1.0


class TestSectorPreference:
    """TDD tests for sector preference."""

    def test_sector_preference(self):
        """Sector preference applied correctly."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech", "energy"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp_match = Opportunity(
            name="Tech Deal",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        opp_no_match = Opportunity(
            name="Healthcare Deal",
            sector="healthcare",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        score_match = matcher.sector_preference(swf, opp_match)
        score_no_match = matcher.sector_preference(swf, opp_no_match)
        assert score_match > score_no_match
        assert 0.0 <= score_match <= 1.0
        assert 0.0 <= score_no_match <= 1.0


class TestHorizonMatching:
    """TDD tests for investment horizon matching."""

    def test_horizon_matching(self):
        """Investment horizon matched correctly."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp = Opportunity(
            name="Tech Deal",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        score = matcher.horizon_matching(swf, opp)
        assert 0.0 <= score <= 1.0


class TestRiskTolerance:
    """TDD tests for risk tolerance scoring."""

    def test_risk_tolerance(self):
        """Risk tolerance scored correctly."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opp = Opportunity(
            name="Tech Deal",
            sector="tech",
            geography="US",
            deal_size=500000.0,
            expected_return=0.15,
            risk_score=0.4,
            trl=7,
        )
        score = matcher.risk_tolerance_score(swf, opp)
        assert 0.0 <= score <= 1.0


class TestMatchReport:
    """TDD tests for match report generation."""

    def test_match_report(self):
        """Match report generated with expected structure."""
        matcher = SWFMatcher()
        swf = matcher.create_profile(
            name="Test Fund",
            aum=1000000.0,
            horizon_years=10,
            risk_tolerance=0.5,
            geographic_focus=["US"],
            sector_focus=["tech"],
            min_deal_size=100000.0,
            max_deal_size=5000000.0,
        )
        opps = [
            Opportunity(
                name="Tech Deal",
                sector="tech",
                geography="US",
                deal_size=500000.0,
                expected_return=0.15,
                risk_score=0.4,
                trl=7,
            ),
        ]
        matches = [matcher.match(swf, opp) for opp in opps]
        report = matcher.generate_match_report(matches)
        assert isinstance(report, dict)
        assert "total_matches" in report
        assert "average_score" in report
        assert "matches" in report
        assert report["total_matches"] == 1
        assert 0.0 <= report["average_score"] <= 1.0
        assert len(report["matches"]) == 1
