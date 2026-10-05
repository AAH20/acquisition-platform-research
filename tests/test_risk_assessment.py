"""Tests for risk assessment module."""
import pytest
from acquisition_platform.risk_assessment import (
    RiskFactor,
    RiskAssessment,
    RiskAssessor,
)


class TestRiskAssessment:
    """TDD tests for the risk assessment module."""

    def test_risk_scoring(self):
        """Multi-factor risk scored correctly."""
        assessor = RiskAssessor()
        factors = [
            assessor.assess_risk("Market Risk", 7.0, 0.3, "market"),
            assessor.assess_risk("Credit Risk", 5.0, 0.4, "credit"),
            assessor.assess_risk("Operational Risk", 3.0, 0.3, "operational"),
        ]
        score = assessor.total_score(factors)
        expected = 7.0 * 0.3 + 5.0 * 0.4 + 3.0 * 0.3
        assert score == pytest.approx(expected)

    def test_geographic_risk(self):
        """Geographic risk weighted by country and region."""
        assessor = RiskAssessor()
        # High-risk country should score higher than low-risk
        high = assessor.geographic_risk("SY", "Middle East")
        low = assessor.geographic_risk("US", "North America")
        assert high > low
        assert 0 <= high <= 10
        assert 0 <= low <= 10

    def test_technology_risk(self):
        """Technology risk weighted by TRL and complexity."""
        assessor = RiskAssessor()
        # Low TRL + high complexity should be riskier than high TRL + low complexity
        risky = assessor.technology_risk(trl=2, complexity=9)
        safe = assessor.technology_risk(trl=9, complexity=2)
        assert risky > safe
        assert 0 <= risky <= 10
        assert 0 <= safe <= 10

    def test_financial_risk(self):
        """Financial risk weighted by leverage and liquidity."""
        assessor = RiskAssessor()
        # High leverage + low liquidity should be riskier
        risky = assessor.financial_risk(leverage=0.9, liquidity=0.1)
        safe = assessor.financial_risk(leverage=0.1, liquidity=0.9)
        assert risky > safe
        assert 0 <= risky <= 10
        assert 0 <= safe <= 10

    def test_hr_risk(self):
        """HR risk weighted by key person dependency and turnover."""
        assessor = RiskAssessor()
        # High dependency + high turnover should be riskier
        risky = assessor.hr_risk(key_person_dependency=0.9, turnover=0.8)
        safe = assessor.hr_risk(key_person_dependency=0.1, turnover=0.1)
        assert risky > safe
        assert 0 <= risky <= 10
        assert 0 <= safe <= 10

    def test_empty_risks(self):
        """Empty risks returns score 0."""
        assessor = RiskAssessor()
        assert assessor.total_score([]) == 0.0

    def test_risk_classification(self):
        """Risk level classified correctly."""
        assessor = RiskAssessor()
        assert assessor.risk_level(2.0) == "low"
        assert assessor.risk_level(5.0) == "medium"
        assert assessor.risk_level(7.5) == "high"
        assert assessor.risk_level(9.5) == "critical"

    def test_risk_portfolio(self):
        """Portfolio risk aggregated from multiple assessments."""
        assessor = RiskAssessor()
        factors_a = [
            assessor.assess_risk("Tech Risk", 6.0, 0.5, "technology"),
            assessor.assess_risk("Market Risk", 4.0, 0.5, "market"),
        ]
        factors_b = [
            assessor.assess_risk("Credit Risk", 8.0, 0.6, "credit"),
            assessor.assess_risk("Ops Risk", 3.0, 0.4, "operational"),
        ]
        report_a = assessor.generate_report(factors_a)
        report_b = assessor.generate_report(factors_b)
        # Portfolio score is weighted average of individual scores
        portfolio_score = (report_a.total_score + report_b.total_score) / 2
        assert portfolio_score > 0
        assert portfolio_score <= 10

    def test_risk_mitigation(self):
        """Mitigation strategies generated for high-risk factors."""
        assessor = RiskAssessor()
        factors = [
            assessor.assess_risk("Market Risk", 8.0, 0.4, "market"),
            assessor.assess_risk("Credit Risk", 7.0, 0.3, "credit"),
            assessor.assess_risk("Operational Risk", 2.0, 0.3, "operational"),
        ]
        mitigations = assessor.generate_mitigations(factors)
        assert len(mitigations) > 0
        # High-risk factors should have mitigations
        assert any("market" in m.lower() or "diversif" in m.lower() for m in mitigations)
        assert any("credit" in m.lower() or "hedge" in m.lower() for m in mitigations)

    def test_risk_report(self):
        """Report generated correctly with all fields."""
        assessor = RiskAssessor()
        factors = [
            assessor.assess_risk("Market Risk", 6.0, 0.4, "market"),
            assessor.assess_risk("Technology Risk", 7.0, 0.3, "technology"),
            assessor.assess_risk("Financial Risk", 5.0, 0.3, "financial"),
        ]
        report = assessor.generate_report(factors)
        assert isinstance(report, RiskAssessment)
        assert len(report.factors) == 3
        assert report.total_score > 0
        assert report.risk_level in ("low", "medium", "high", "critical")
        assert isinstance(report.mitigations, list)
