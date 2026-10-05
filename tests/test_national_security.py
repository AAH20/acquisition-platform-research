"""Tests for the national security screening module."""
from acquisition_platform.national_security import (
    NationalSecurityScreener,
    ScreeningResult,
)


class TestNationalSecurityScreener:
    """TDD tests for the national security screener."""

    def test_cfius_screening(self):
        """CFIUS risk should be scored for a portfolio of items."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen(
                technology_id="TECH-001",
                name="Advanced AI Compute",
                tid=True,
                foreign_investor=True,
                government_investor=False,
                clearance_required="secret",
            ),
            screener.screen(
                technology_id="TECH-002",
                name="Public Software",
                tid=False,
                foreign_investor=False,
                government_investor=False,
                clearance_required="none",
            ),
        ]
        risk = screener.cfius_risk(items)
        assert 0.0 < risk <= 1.0

        # Fully clean portfolio carries no CFIUS risk
        clean = [
            screener.screen("T1", "Clean A", False, False, False, "none"),
            screener.screen("T2", "Clean B", False, False, False, "none"),
        ]
        assert screener.cfius_risk(clean) == 0.0

        # More exposed items produce higher CFIUS risk
        high = [
            screener.screen("T1", "TID Gov", True, True, True, "top_secret"),
            screener.screen("T2", "TID Gov B", True, True, True, "top_secret"),
        ]
        assert screener.cfius_risk(high) > risk

    def test_fdi_screening(self):
        """FDI risk should be assessed across foreign investors."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen("T1", "Strategic Tech", True, True, False, "secret"),
            screener.screen("T2", "Data Platform", True, True, True, "top_secret"),
        ]
        risk = screener.fdi_risk(items, ["CN", "RU"])
        assert 0.0 < risk <= 1.0

        # Lower-risk jurisdictions reduce FDI risk
        low_risk = screener.fdi_risk(items, ["US", "GB"])
        assert low_risk < risk

        # No foreign exposure -> no FDI risk
        domestic = [screener.screen("T1", "Domestic", True, False, False, "none")]
        assert screener.fdi_risk(domestic, ["CN"]) == 0.0

    def test_tid_business(self):
        """TID business status should be detected."""
        screener = NationalSecurityScreener()
        tid_items = [screener.screen("T1", "Semiconductor Fab", True, False, False, "none")]
        assert screener.is_tid_business(tid_items) is True

        non_tid = [screener.screen("T1", "Marketing Site", False, False, False, "none")]
        assert screener.is_tid_business(non_tid) is False

    def test_security_clearance(self):
        """Clearance requirements should be collected and deduplicated."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen("T1", "Radar", True, False, False, "secret"),
            screener.screen("T2", "Comms", True, False, False, "top_secret"),
            screener.screen("T3", "Public", False, False, False, "none"),
        ]
        reqs = screener.clearance_requirements(items)
        assert "secret" in reqs
        assert "top_secret" in reqs
        assert "none" not in reqs
        assert len(reqs) == len(set(reqs))

    def test_empty_screening(self):
        """Empty screening should return safe defaults."""
        screener = NationalSecurityScreener()
        assert screener.cfius_risk([]) == 0.0
        assert screener.fdi_risk([], ["CN"]) == 0.0
        assert screener.is_tid_business([]) is False
        assert screener.clearance_requirements([]) == []
        assert screener.mandatory_filing_required([]) is False
        assert screener.generate_mitigation_plan([]) == []

        report = screener.generate_screening_report([])
        assert isinstance(report, ScreeningResult)
        assert report.items == []
        assert report.cfius_risk == 0.0
        assert report.fdi_risk == 0.0
        assert report.clearance_required is False
        assert report.filing_required is False
        assert report.mitigation_plan == []

    def test_cross_border_screening(self):
        """Multi-country screening should aggregate jurisdiction risk."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen("T1", "AI Chip Design", True, True, False, "secret"),
            screener.screen("T2", "Cloud Data Center", True, True, False, "none"),
        ]
        high_risk = screener.fdi_risk(items, ["CN", "RU", "IR"])
        mixed_risk = screener.fdi_risk(items, ["CN", "DE"])
        low_risk = screener.fdi_risk(items, ["US", "CA"])
        assert high_risk > mixed_risk > low_risk

    def test_mandatory_filing(self):
        """Mandatory CFIUS filing should be flagged for TID + foreign control."""
        screener = NationalSecurityScreener()
        mandatory = [
            screener.screen("T1", "Defense Tech", True, True, False, "top_secret"),
        ]
        assert screener.mandatory_filing_required(mandatory) is True

        # TID without a foreign investor does not trigger mandatory filing
        tid_only = [screener.screen("T1", "Domestic Fab", True, False, False, "none")]
        assert screener.mandatory_filing_required(tid_only) is False

        # Government investor triggers mandatory filing regardless
        gov = [screener.screen("T1", "State Backed", False, False, True, "none")]
        assert screener.mandatory_filing_required(gov) is True

    def test_mitigation_plan(self):
        """A mitigation plan should be generated for risky portfolios."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen("T1", "TID Gov Tech", True, True, True, "top_secret"),
        ]
        plan = screener.generate_mitigation_plan(items)
        assert isinstance(plan, list)
        assert len(plan) > 0
        assert all(isinstance(step, str) for step in plan)

    def test_screening_report(self):
        """A full screening report should be generated."""
        screener = NationalSecurityScreener()
        items = [
            screener.screen("T1", "AI Model", True, True, False, "secret"),
            screener.screen("T2", "Open Source Tool", False, False, False, "none"),
        ]
        report = screener.generate_screening_report(items)
        assert isinstance(report, ScreeningResult)
        assert len(report.items) == 2
        assert 0.0 <= report.cfius_risk <= 1.0
        assert 0.0 <= report.fdi_risk <= 1.0
        assert isinstance(report.clearance_required, bool)
        assert isinstance(report.filing_required, bool)
        assert isinstance(report.mitigation_plan, list)
        assert report.filing_required is True

    def test_political_risk(self):
        """Political risk should be assessed by country and region."""
        screener = NationalSecurityScreener()
        high = screener.political_risk("CN", "east_asia")
        low = screener.political_risk("US", "north_america")
        assert 0.0 <= high <= 1.0
        assert 0.0 <= low <= 1.0
        assert high > low
        # Region modifier should matter for the same country
        assert screener.political_risk("US", "middle_east") > low
