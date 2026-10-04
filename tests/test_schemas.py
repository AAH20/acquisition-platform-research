"""Tests for shared schemas module."""
import pytest
from acquisition_platform.schemas import (
    Category,
    Confidence,
    Money,
    RiskLevel,
    clamp,
    classify_risk,
    format_money,
)


class TestClamp:
    """Tests for the clamp utility function."""

    def test_clamp_within_range(self):
        assert clamp(5, 0, 10) == 5

    def test_clamp_below_min(self):
        assert clamp(-5, 0, 10) == 0

    def test_clamp_above_max(self):
        assert clamp(15, 0, 10) == 10

    def test_clamp_at_min_boundary(self):
        assert clamp(0, 0, 10) == 0

    def test_clamp_at_max_boundary(self):
        assert clamp(10, 0, 10) == 10

    def test_clamp_negative_range(self):
        assert clamp(-5, -10, -1) == -5

    def test_clamp_negative_below_min(self):
        assert clamp(-15, -10, -1) == -10

    def test_clamp_negative_above_max(self):
        assert clamp(0, -10, -1) == -1

    def test_clamp_float_values(self):
        assert clamp(3.7, 0.0, 1.0) == 1.0

    def test_clamp_zero_range(self):
        assert clamp(5, 7, 7) == 7


class TestClassifyRisk:
    """Tests for the classify_risk utility function."""

    def test_classify_risk_low(self):
        assert classify_risk(0.1) == RiskLevel.LOW

    def test_classify_risk_medium(self):
        assert classify_risk(0.4) == RiskLevel.MEDIUM

    def test_classify_risk_high(self):
        assert classify_risk(0.7) == RiskLevel.HIGH

    def test_classify_risk_critical(self):
        assert classify_risk(0.95) == RiskLevel.CRITICAL

    def test_classify_risk_boundary_low_medium(self):
        assert classify_risk(0.3) == RiskLevel.MEDIUM

    def test_classify_risk_boundary_medium_high(self):
        assert classify_risk(0.6) == RiskLevel.HIGH

    def test_classify_risk_boundary_high_critical(self):
        assert classify_risk(0.9) == RiskLevel.CRITICAL

    def test_classify_risk_zero(self):
        assert classify_risk(0.0) == RiskLevel.LOW

    def test_classify_risk_one(self):
        assert classify_risk(1.0) == RiskLevel.CRITICAL

    def test_classify_risk_negative_clamped(self):
        assert classify_risk(-0.5) == RiskLevel.LOW

    def test_classify_risk_above_one_clamped(self):
        assert classify_risk(1.5) == RiskLevel.CRITICAL


class TestMoney:
    """Tests for the Money value object."""

    def test_money_creation(self):
        m = Money(amount=100.50, currency="USD")
        assert m.amount == 100.50
        assert m.currency == "USD"

    def test_money_equality(self):
        m1 = Money(amount=100, currency="USD")
        m2 = Money(amount=100, currency="USD")
        assert m1 == m2

    def test_money_inequality_amount(self):
        m1 = Money(amount=100, currency="USD")
        m2 = Money(amount=200, currency="USD")
        assert m1 != m2

    def test_money_inequality_currency(self):
        m1 = Money(amount=100, currency="USD")
        m2 = Money(amount=100, currency="EUR")
        assert m1 != m2

    def test_money_zero_amount(self):
        m = Money(amount=0, currency="USD")
        assert m.amount == 0

    def test_money_negative_amount(self):
        m = Money(amount=-50, currency="USD")
        assert m.amount == -50

    def test_money_different_currencies(self):
        m = Money(amount=100, currency="GBP")
        assert m.currency == "GBP"

    def test_money_repr(self):
        m = Money(amount=100, currency="USD")
        assert "100" in repr(m)
        assert "USD" in repr(m)


class TestConfidence:
    """Tests for the Confidence value object."""

    def test_confidence_creation(self):
        c = Confidence(score=0.85, level="high")
        assert c.score == 0.85
        assert c.level == "high"

    def test_confidence_equality(self):
        c1 = Confidence(score=0.7, level="medium")
        c2 = Confidence(score=0.7, level="medium")
        assert c1 == c2

    def test_confidence_inequality_score(self):
        c1 = Confidence(score=0.7, level="medium")
        c2 = Confidence(score=0.8, level="medium")
        assert c1 != c2

    def test_confidence_inequality_level(self):
        c1 = Confidence(score=0.7, level="medium")
        c2 = Confidence(score=0.7, level="high")
        assert c1 != c2

    def test_confidence_zero_score(self):
        c = Confidence(score=0.0, level="none")
        assert c.score == 0.0

    def test_confidence_max_score(self):
        c = Confidence(score=1.0, level="certain")
        assert c.score == 1.0

    def test_confidence_various_levels(self):
        c1 = Confidence(score=0.2, level="low")
        c2 = Confidence(score=0.5, level="medium")
        c3 = Confidence(score=0.9, level="high")
        assert c1.level == "low"
        assert c2.level == "medium"
        assert c3.level == "high"

    def test_confidence_repr(self):
        c = Confidence(score=0.75, level="medium")
        assert "0.75" in repr(c)
        assert "medium" in repr(c)


class TestCategoryEnum:
    """Tests for the Category enum."""

    def test_category_values(self):
        assert Category.SAAS.value == "saas"
        assert Category.ECOMMERCE.value == "ecommerce"
        assert Category.CONTENT.value == "content"
        assert Category.SERVICE.value == "service"
        assert Category.OTHER.value == "other"

    def test_category_members_count(self):
        assert len(Category) == 5

    def test_category_lookup_by_value(self):
        assert Category("saas") == Category.SAAS
        assert Category("ecommerce") == Category.ECOMMERCE

    def test_category_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Category("invalid")

    def test_category_string_representation(self):
        assert str(Category.SAAS) == "Category.SAAS"


class TestRiskLevelEnum:
    """Tests for the RiskLevel enum."""

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_level_members_count(self):
        assert len(RiskLevel) == 4

    def test_risk_level_lookup_by_value(self):
        assert RiskLevel("low") == RiskLevel.LOW
        assert RiskLevel("critical") == RiskLevel.CRITICAL

    def test_risk_level_invalid_value_raises(self):
        with pytest.raises(ValueError):
            RiskLevel("extreme")

    def test_risk_level_ordering(self):
        levels = list(RiskLevel)
        assert levels == [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestFormatMoney:
    """Tests for the format_money utility function."""

    def test_format_money_usd(self):
        result = format_money(1000, "USD")
        assert "$" in result
        assert "1,000" in result

    def test_format_money_eur(self):
        result = format_money(500, "EUR")
        assert "€" in result
        assert "500" in result

    def test_format_money_gbp(self):
        result = format_money(250, "GBP")
        assert "£" in result
        assert "250" in result

    def test_format_money_jpy(self):
        result = format_money(10000, "JPY")
        assert "¥" in result
        assert "10,000" in result

    def test_format_money_zero(self):
        result = format_money(0, "USD")
        assert "$" in result
        assert "0" in result

    def test_format_money_negative(self):
        result = format_money(-100, "USD")
        assert "-" in result
        assert "100" in result

    def test_format_money_with_cents(self):
        result = format_money(99.99, "USD")
        assert "$" in result
        assert "99.99" in result

    def test_format_money_large_amount(self):
        result = format_money(1000000, "USD")
        assert "1,000,000" in result

    def test_format_money_unknown_currency(self):
        result = format_money(100, "XYZ")
        assert "100" in result
        assert "XYZ" in result
