"""Tests for IP/patent valuation module."""
import pytest

from acquisition_platform.exceptions import (
    DivisionByZeroError,
    InvalidRangeError,
    ValidationError,
)
from acquisition_platform.ip_valuation import (
    IPValuator,
    Patent,
    PatentPortfolio,
)


def _make_patent(
    patent_id: str = "US-1234567",
    title: str = "Method for wireless communication",
    status: str = "granted",
    citations: int = 50,
    filed_date: str = "2018-01-15",
    granted_date: str = "2020-06-01",
) -> Patent:
    return Patent(
        patent_id=patent_id,
        title=title,
        status=status,
        citations=citations,
        filed_date=filed_date,
        granted_date=granted_date,
    )


class TestIPValuation:
    """TDD tests for the IP valuation module."""

    def test_patent_valuation(self):
        valuator = IPValuator()
        patent = _make_patent()
        value = valuator.value_patent(patent)
        assert value > 0
        # RFR: base 100k * citation_impact(50)=1.5 * granted(1.0) = 150k
        assert value == pytest.approx(150_000.0)

    def test_portfolio_valuation(self):
        valuator = IPValuator()
        patents = [
            _make_patent(patent_id="P1", citations=50),
            _make_patent(patent_id="P2", citations=30),
            _make_patent(patent_id="P3", citations=10),
        ]
        portfolio = valuator.value_portfolio(patents)
        assert isinstance(portfolio, PatentPortfolio)
        assert portfolio.total_value > 0
        expected = sum(valuator.value_patent(p) for p in patents)
        assert portfolio.total_value == pytest.approx(expected)
        assert len(portfolio.patents) == 3

    def test_citation_impact(self):
        valuator = IPValuator()
        assert valuator.citation_impact(0) == pytest.approx(1.0)
        assert valuator.citation_impact(50) == pytest.approx(1.5)
        assert valuator.citation_impact(100) == pytest.approx(2.0)
        # Capped at 100 citations
        assert valuator.citation_impact(500) == pytest.approx(2.0)

    def test_granted_vs_pending(self):
        valuator = IPValuator()
        assert valuator.granted_vs_pending("granted") == pytest.approx(1.0)
        assert valuator.granted_vs_pending("pending") == pytest.approx(0.5)
        assert valuator.granted_vs_pending("expired") == pytest.approx(0.1)

    def test_empty_portfolio(self):
        valuator = IPValuator()
        portfolio = valuator.value_portfolio([])
        assert portfolio.total_value == 0.0
        assert portfolio.fto_score == 1.0
        assert portfolio.thicket_detected is False
        assert portfolio.patents == []

    def test_relief_from_royalty(self):
        valuator = IPValuator()
        patent = _make_patent(citations=50, status="granted")
        value = valuator.value_patent(patent)
        # RFR formula: base_value * citation_impact * status_multiplier
        expected = 100_000 * 1.5 * 1.0
        assert value == pytest.approx(expected)

    def test_income_approach(self):
        valuator = IPValuator()
        value = valuator.income_approach(
            revenue=1_000_000, margin=0.3, discount_rate=0.1
        )
        assert value == pytest.approx(3_000_000.0)

    def test_market_approach(self):
        valuator = IPValuator()
        value = valuator.market_approach(comps_multiple=3.5, revenue=1_000_000)
        assert value == pytest.approx(3_500_000.0)

    def test_patent_thicket_detected(self):
        valuator = IPValuator()
        # Patents with overlapping titles form a thicket
        thicket_patents = [
            _make_patent(patent_id="T1", title="Wireless communication system"),
            _make_patent(patent_id="T2", title="Wireless communication method"),
            _make_patent(patent_id="T3", title="Wireless communication protocol"),
        ]
        assert valuator.thicket_detected(thicket_patents) is True

        # Non-overlapping patents do not form a thicket
        diverse_patents = [
            _make_patent(patent_id="D1", title="Wireless communication system"),
            _make_patent(patent_id="D2", title="Semiconductor fabrication process"),
            _make_patent(patent_id="D3", title="Battery charging circuit"),
        ]
        assert valuator.thicket_detected(diverse_patents) is False

    def test_fto_score(self):
        valuator = IPValuator()
        patents = [
            _make_patent(patent_id="F1", title="Wireless communication system"),
            _make_patent(patent_id="F2", title="Semiconductor fabrication process"),
        ]
        # No competitor patents -> full freedom to operate
        assert valuator.fto_score(patents, []) == pytest.approx(1.0)

        # Competitor patent overlapping with one of ours
        competitor = [
            _make_patent(patent_id="C1", title="Wireless communication method"),
        ]
        score = valuator.fto_score(patents, competitor)
        assert 0.0 <= score < 1.0
        # 1 of 2 patents overlaps -> score = 0.5
        assert score == pytest.approx(0.5)

    def test_income_approach_zero_discount_rate(self):
        valuator = IPValuator()
        with pytest.raises(DivisionByZeroError):
            valuator.income_approach(revenue=1_000_000, margin=0.3, discount_rate=0.0)

    def test_income_approach_negative_revenue(self):
        valuator = IPValuator()
        with pytest.raises(ValidationError):
            valuator.income_approach(revenue=-100, margin=0.3, discount_rate=0.1)

    def test_income_approach_invalid_margin(self):
        valuator = IPValuator()
        with pytest.raises(InvalidRangeError):
            valuator.income_approach(revenue=1_000_000, margin=1.5, discount_rate=0.1)

    def test_market_approach_negative_revenue(self):
        valuator = IPValuator()
        with pytest.raises(ValidationError):
            valuator.market_approach(comps_multiple=3.5, revenue=-100)

    def test_value_patent_pending_worth_less(self):
        valuator = IPValuator()
        granted = _make_patent(status="granted", citations=50)
        pending = _make_patent(status="pending", citations=50)
        assert valuator.value_patent(granted) > valuator.value_patent(pending)

    def test_value_patent_more_citations_worth_more(self):
        valuator = IPValuator()
        low_cite = _make_patent(citations=5)
        high_cite = _make_patent(citations=80)
        assert valuator.value_patent(high_cite) > valuator.value_patent(low_cite)

    def test_portfolio_includes_fto_and_thicket(self):
        valuator = IPValuator()
        patents = [
            _make_patent(patent_id="P1", title="Wireless communication system"),
            _make_patent(patent_id="P2", title="Wireless communication method"),
            _make_patent(patent_id="P3", title="Wireless communication protocol"),
        ]
        portfolio = valuator.value_portfolio(patents)
        assert portfolio.thicket_detected is True
        assert portfolio.fto_score == pytest.approx(1.0)
