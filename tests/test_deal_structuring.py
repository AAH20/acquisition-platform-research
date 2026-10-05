"""Tests for deal structuring module."""
import pytest

from acquisition_platform.deal_structuring import (
    CVR,
    DealStructure,
    DealStructurer,
    Earnout,
)


class TestDealStructurer:
    """TDD tests for the deal structuring module."""

    def test_earnout_valuation(self):
        structurer = DealStructurer()
        earnout = Earnout(
            target_revenue=1_000_000,
            target_profit=200_000,
            max_payout=500_000,
            probability=0.6,
        )
        value = structurer.value_earnout(earnout)
        assert value == pytest.approx(300_000)

    def test_cvr_valuation(self):
        structurer = DealStructurer()
        cvrs = [
            CVR(milestone="FDA approval", payout=1_000_000, probability=0.4),
            CVR(milestone="Revenue milestone", payout=500_000, probability=0.7),
        ]
        value = structurer.value_cvr(cvrs)
        assert value == pytest.approx(750_000)

    def test_escrow_calculation(self):
        structurer = DealStructurer()
        escrow = structurer.calculate_escrow(purchase_price=1_000_000, risk_score=0.5)
        assert escrow == pytest.approx(125_000)

    def test_indemnification_cap(self):
        structurer = DealStructurer()
        cap = structurer.set_indemnification_cap(purchase_price=1_000_000, risk_score=0.5)
        assert cap == pytest.approx(200_000)

    def test_empty_structure(self):
        structurer = DealStructurer()
        report = structurer.generate_structure_report(DealStructure())
        assert report["purchase_price"] == 0.0
        assert report["earnout_value"] == 0.0
        assert report["cvr_value"] == 0.0
        assert report["escrow"] == 0.0
        assert report["indemnification_cap"] == 0.0
        assert report["total_consideration"] == 0.0

    def test_cross_border_structure(self):
        structurer = DealStructurer()
        structure = DealStructure(
            purchase_price=1_000_000,
            escrow=100_000,
            indemnification_cap=150_000,
        )
        adjusted = structurer.cross_border_adjustment(structure, country_risk=0.25)
        assert adjusted.escrow == pytest.approx(125_000)
        assert adjusted.indemnification_cap == pytest.approx(187_500)
        assert adjusted.purchase_price == 1_000_000

    def test_regulatory_holdback(self):
        structurer = DealStructurer()
        holdback = structurer.regulatory_holdback(
            purchase_price=2_000_000, regulatory_risk=0.5
        )
        assert holdback == pytest.approx(150_000)

    def test_earnout_probability(self):
        structurer = DealStructurer()
        earnout = Earnout(
            target_revenue=800_000,
            target_profit=150_000,
            max_payout=400_000,
            probability=0.75,
        )
        value = structurer.probability_weighted_earnout(earnout)
        assert value == pytest.approx(300_000)

    def test_deal_structure_report(self):
        structurer = DealStructurer()
        structure = DealStructure(
            purchase_price=5_000_000,
            earnout=Earnout(
                target_revenue=2_000_000,
                target_profit=400_000,
                max_payout=1_000_000,
                probability=0.5,
            ),
            cvr=[CVR(milestone="Milestone 1", payout=500_000, probability=0.5)],
            escrow=250_000,
            indemnification_cap=500_000,
        )
        report = structurer.generate_structure_report(structure)
        assert report["purchase_price"] == 5_000_000
        assert report["earnout_value"] == pytest.approx(500_000)
        assert report["cvr_value"] == pytest.approx(250_000)
        assert report["escrow"] == 250_000
        assert report["indemnification_cap"] == 500_000
        assert report["total_consideration"] == pytest.approx(5_750_000)

    def test_synergy_valuation(self):
        structurer = DealStructurer()
        value = structurer.value_synergies(
            revenue_synergies=100_000,
            cost_synergies=50_000,
            discount_rate=0.10,
        )
        assert value == pytest.approx(1_500_000)
