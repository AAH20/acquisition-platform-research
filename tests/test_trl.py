"""Tests for TRL (Technology Readiness Level) assessment module."""
import pytest
from acquisition_platform.trl import TRLAssessment, TRLPortfolio, TRLAssessor
from acquisition_platform.exceptions import ValidationError


class TestTRLAssessment:
    """TDD tests for the TRL assessment module."""

    def test_trl_level_1_to_9(self):
        """All valid TRL levels 1-9 are accepted."""
        assessor = TRLAssessor()
        for level in range(1, 10):
            result = assessor.assess(
                technology_id=f"tech-{level}",
                name=f"Technology {level}",
                trl_level=level,
                category="test",
            )
            assert result.trl_level == level
            assert result.technology_id == f"tech-{level}"
            assert result.name == f"Technology {level}"
            assert result.category == "test"

    def test_trl_below_1_raises(self):
        """TRL < 1 raises ValidationError."""
        assessor = TRLAssessor()
        with pytest.raises(ValidationError):
            assessor.assess("tech-x", "Bad Tech", 0, "test")

    def test_trl_above_9_raises(self):
        """TRL > 9 raises ValidationError."""
        assessor = TRLAssessor()
        with pytest.raises(ValidationError):
            assessor.assess("tech-x", "Bad Tech", 10, "test")

    def test_trl_valuation_multiplier(self):
        """Higher TRL = higher multiplier."""
        assessor = TRLAssessor()
        low = assessor.valuation_multiplier(1)
        high = assessor.valuation_multiplier(9)
        assert high > low
        assert low == pytest.approx(0.05)
        assert high == pytest.approx(1.0)

    def test_trl_risk_premium(self):
        """Higher TRL = lower risk premium."""
        assessor = TRLAssessor()
        low = assessor.risk_premium(1)
        high = assessor.risk_premium(9)
        assert high < low
        assert low == pytest.approx(0.15)
        assert high == pytest.approx(0.02)

    def test_trl_portfolio_score(self):
        """Aggregate TRL score for portfolio."""
        assessor = TRLAssessor()
        assessments = [
            assessor.assess("t1", "Tech A", 3, "test"),
            assessor.assess("t2", "Tech B", 7, "test"),
        ]
        portfolio = assessor.portfolio_score(assessments)
        assert isinstance(portfolio, TRLPortfolio)
        assert portfolio.portfolio_score == pytest.approx(5 / 9)  # avg(3,7)/9 = 5/9
        assert portfolio.risk_adjusted_wacc > 0

    def test_trl_classification(self):
        """Classify technology by TRL."""
        assessor = TRLAssessor()
        assert assessor.classify(1) == "basic_research"
        assert assessor.classify(2) == "basic_research"
        assert assessor.classify(3) == "basic_research"
        assert assessor.classify(4) == "development_validation"
        assert assessor.classify(5) == "development_validation"
        assert assessor.classify(6) == "development_validation"
        assert assessor.classify(7) == "deployment"
        assert assessor.classify(8) == "deployment"
        assert assessor.classify(9) == "proven_in_operation"

    def test_trl_empty_portfolio(self):
        """Empty portfolio returns score 0."""
        assessor = TRLAssessor()
        portfolio = assessor.portfolio_score([])
        assert portfolio.portfolio_score == 0.0
        assert portfolio.risk_adjusted_wacc == 0.0

    def test_trl_mixed_portfolio(self):
        """Mixed TRL levels scored correctly."""
        assessor = TRLAssessor()
        assessments = [
            assessor.assess("t1", "Tech A", 1, "test"),
            assessor.assess("t2", "Tech B", 5, "test"),
            assessor.assess("t3", "Tech C", 9, "test"),
        ]
        portfolio = assessor.portfolio_score(assessments)
        # avg(1,5,9) = 5, normalized = 5/9 ≈ 0.556
        assert portfolio.portfolio_score == pytest.approx(5 / 9)

    def test_trl_wacc_adjustment(self):
        """WACC adjusted by TRL."""
        assessor = TRLAssessor()
        base = 0.10
        low_trl_wacc = assessor.adjust_wacc(base, 1)
        high_trl_wacc = assessor.adjust_wacc(base, 9)
        assert low_trl_wacc > high_trl_wacc
        assert low_trl_wacc == pytest.approx(base + 0.15)
        assert high_trl_wacc == pytest.approx(base + 0.02)
