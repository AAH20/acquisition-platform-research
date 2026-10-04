"""Tests for cross-border deal optimization module."""
import pytest

from acquisition_platform.cross_border import (
    Jurisdiction,
    RegulatoryFiling,
    CrossBorderDeal,
    CrossBorderResult,
    CrossBorderOptimizer,
)


class TestCrossBorderOptimizer:
    """TDD tests for the cross-border deal optimizer."""

    def test_regulatory_filing_sequence(self):
        """Filings should be in correct order (by deadline, dependencies first)."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        filings = optimizer.coordinate_regulatory(deal)
        assert len(filings) > 0
        # Filings must be sorted by deadline
        deadlines = [f.deadline for f in filings]
        assert deadlines == sorted(deadlines)
        # Dependencies must appear before the filings that depend on them
        filing_types = [f.filing_type for f in filings]
        for f in filings:
            for dep in f.dependencies:
                assert dep in filing_types
                dep_idx = filing_types.index(dep)
                f_idx = filing_types.index(f.filing_type)
                assert dep_idx < f_idx

    def test_tax_optimization(self):
        """Tax optimization should minimize tax burden below naive sum."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        total_tax = optimizer.optimize_tax(deal)
        # Naive tax: (0.21 + 0.30) * 100M = 51M
        naive_tax = sum(j.tax_rate for j in jurisdictions) * deal.deal_value
        assert total_tax < naive_tax
        assert total_tax > 0

    def test_currency_hedging(self):
        """Currency hedging cost should scale with number of jurisdictions."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        hedging_cost = optimizer.hedge_currency(deal)
        assert hedging_cost > 0
        # More jurisdictions = more hedging cost
        single_deal = CrossBorderDeal(
            jurisdictions=[jurisdictions[0]], deal_value=100_000_000, deal_type="acquisition"
        )
        single_cost = optimizer.hedge_currency(single_deal)
        assert hedging_cost > single_cost

    def test_integration_planning(self):
        """Integration timeline should scale with jurisdictions."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        timeline = optimizer.plan_integration(deal)
        assert timeline > 0
        # More jurisdictions = longer timeline
        single_deal = CrossBorderDeal(
            jurisdictions=[jurisdictions[0]], deal_value=100_000_000, deal_type="acquisition"
        )
        single_timeline = optimizer.plan_integration(single_deal)
        assert timeline > single_timeline

    def test_multi_jurisdiction(self):
        """Deal spanning multiple countries should generate filings for all."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
            Jurisdiction(code="JP", name="Japan", regulatory_body="METI", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        result = optimizer.optimize(deal)
        assert len(result.filings) > 0
        filing_jurisdictions = {f.jurisdiction for f in result.filings}
        assert "US" in filing_jurisdictions
        assert "DE" in filing_jurisdictions
        assert "JP" in filing_jurisdictions

    def test_fdi_screening(self):
        """FDI screening should generate appropriate filings."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        filings = optimizer.coordinate_regulatory(deal)
        fdi_filings = [
            f
            for f in filings
            if "fdi" in f.filing_type.lower() or "foreign_investment" in f.filing_type.lower()
        ]
        assert len(fdi_filings) > 0

    def test_empty_jurisdictions(self):
        """No jurisdictions should return empty plan."""
        optimizer = CrossBorderOptimizer()
        deal = CrossBorderDeal(jurisdictions=[], deal_value=100_000_000, deal_type="acquisition")
        result = optimizer.optimize(deal)
        assert result.filings == []
        assert result.total_tax == 0.0
        assert result.hedging_cost == 0.0
        assert result.integration_timeline == 0.0
        assert result.risk_score == 0.0

    def test_single_jurisdiction(self):
        """Single country deal should generate single set of filings."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        result = optimizer.optimize(deal)
        assert len(result.filings) > 0
        filing_jurisdictions = {f.jurisdiction for f in result.filings}
        assert filing_jurisdictions == {"US"}

    def test_treaty_optimization(self):
        """Tax treaty optimization should reduce tax below max-rate baseline."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        total_tax = optimizer.optimize_tax(deal)
        # With treaty optimization, tax should not exceed the max single rate
        max_rate = max(j.tax_rate for j in jurisdictions)
        min_possible = max_rate * deal.deal_value
        assert total_tax <= min_possible * 1.01
        assert total_tax > 0

    def test_synergy_estimation(self):
        """Cross-border synergies should produce a valid risk score."""
        optimizer = CrossBorderOptimizer()
        jurisdictions = [
            Jurisdiction(code="US", name="United States", regulatory_body="CFIUS", tax_rate=0.21),
            Jurisdiction(code="DE", name="Germany", regulatory_body="BMWK", tax_rate=0.30),
        ]
        deal = CrossBorderDeal(
            jurisdictions=jurisdictions, deal_value=100_000_000, deal_type="acquisition"
        )
        result = optimizer.optimize(deal)
        # Risk score is a normalized [0, 1] measure of deal risk
        assert result.risk_score >= 0.0
        assert result.risk_score <= 1.0
