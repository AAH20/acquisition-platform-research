"""Tests for cross-border M&A deal analyzer module (TDD)."""
import pytest

from acquisition_platform.cross_border import (
    CrossBorderAnalyzer,
    CrossBorderDeal,
    CrossBorderResult,
)


class TestCrossBorderAnalyzer:
    """TDD tests for the cross-border M&A analyzer."""

    def test_currency_risk(self):
        """Currency risk should be assessed."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        risk = analyzer.assess_currency_risk(deal)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.0  # EUR has non-zero volatility

    def test_regulatory_risk(self):
        """Regulatory risk should be scored."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        risk = analyzer.assess_regulatory_risk(deal)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.0

    def test_empty_cross_border(self):
        """Empty deal should return default values."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="",
            target_country="",
            deal_value=0.0,
            currency="",
            industry="",
        )
        assert analyzer.assess_currency_risk(deal) == 0.0
        assert analyzer.assess_regulatory_risk(deal) == 0.0
        assert analyzer.tax_optimization(deal) == 0.0
        assert analyzer.cultural_distance("", "") == 0.0
        assert analyzer.treaty_benefits("", "") == []
        assert analyzer.cross_border_timeline(deal) == 0

    def test_tax_optimization(self):
        """Tax optimization should be scored."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        score = analyzer.tax_optimization(deal)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # US and DE have different tax rates

    def test_cultural_distance(self):
        """Cultural distance should be calculated."""
        analyzer = CrossBorderAnalyzer()
        distance = analyzer.cultural_distance("US", "DE")
        assert 0.0 <= distance <= 1.0
        assert distance > 0.0
        # Same country should have zero distance
        assert analyzer.cultural_distance("US", "US") == 0.0

    def test_cross_border_report(self):
        """Report should be generated with all fields."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        result = analyzer.generate_cross_border_report(deal)
        assert isinstance(result, CrossBorderResult)
        assert result.deal == deal
        assert 0.0 <= result.currency_risk <= 1.0
        assert 0.0 <= result.regulatory_risk <= 1.0
        assert 0.0 <= result.tax_optimization <= 1.0
        assert 0.0 <= result.cultural_distance <= 1.0
        assert result.timeline_months > 0

    def test_deal_structure(self):
        """Deal structure should be recommended."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        structure = analyzer.recommend_deal_structure(deal)
        assert isinstance(structure, str)
        assert len(structure) > 0

    def test_financing_strategy(self):
        """Financing strategy should be scored."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        strategy = analyzer.financing_strategy(deal)
        assert isinstance(strategy, str)
        assert len(strategy) > 0

    def test_treaty_benefits(self):
        """Treaty benefits should be assessed."""
        analyzer = CrossBorderAnalyzer()
        benefits = analyzer.treaty_benefits("US", "DE")
        assert isinstance(benefits, list)
        assert len(benefits) > 0
        assert all(isinstance(b, str) for b in benefits)

    def test_cross_border_timeline(self):
        """Timeline should be generated."""
        analyzer = CrossBorderAnalyzer()
        deal = CrossBorderDeal(
            acquirer_country="US",
            target_country="DE",
            deal_value=100_000_000,
            currency="EUR",
            industry="technology",
        )
        timeline = analyzer.cross_border_timeline(deal)
        assert isinstance(timeline, int)
        assert timeline > 0
