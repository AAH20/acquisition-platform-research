"""Tests for valuation engine module."""
import pytest
from acquisition_platform.valuation import ValuationEngine, ValuationResult


class TestValuationEngine:
    """TDD tests for the valuation engine."""

    def test_dcf_valuation_basic(self):
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=100000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            years=5,
        )
        assert result.value > 0
        assert result.method == "DCF"

    def test_dcf_higher_growth_increases_value(self):
        engine = ValuationEngine()
        low_growth = engine.dcf_valuation(
            free_cash_flow=100000, growth_rate=0.02, discount_rate=0.10,
            terminal_growth=0.01, years=5,
        )
        high_growth = engine.dcf_valuation(
            free_cash_flow=100000, growth_rate=0.08, discount_rate=0.10,
            terminal_growth=0.03, years=5,
        )
        assert high_growth.value > low_growth.value

    def test_dcf_higher_discount_rate_decreases_value(self):
        engine = ValuationEngine()
        low_rate = engine.dcf_valuation(
            free_cash_flow=100000, growth_rate=0.05, discount_rate=0.08,
            terminal_growth=0.02, years=5,
        )
        high_rate = engine.dcf_valuation(
            free_cash_flow=100000, growth_rate=0.05, discount_rate=0.15,
            terminal_growth=0.02, years=5,
        )
        assert low_rate.value > high_rate.value

    def test_comparable_company_valuation(self):
        engine = ValuationEngine()
        result = engine.comparable_valuation(
            metric=1000000,  # Revenue
            multiple=3.2,     # EV/Revenue multiple
        )
        assert result.value == 3200000
        assert result.method == "Comps"

    def test_ensemble_valuation_returns_multiple_methods(self):
        engine = ValuationEngine()
        result = engine.ensemble_valuation(
            free_cash_flow=100000,
            revenue=500000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            revenue_multiple=3.2,
            years=5,
        )
        assert result.value > 0
        assert result.method == "Ensemble"
        assert result.confidence > 0

    def test_valuation_result_has_confidence_interval(self):
        engine = ValuationEngine()
        result = engine.ensemble_valuation(
            free_cash_flow=100000,
            revenue=500000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            revenue_multiple=3.2,
            years=5,
        )
        assert result.low_estimate < result.value < result.high_estimate

    def test_sde_multiple_valuation(self):
        engine = ValuationEngine()
        result = engine.sde_valuation(sde=50000, multiple=3.9)
        assert result.value == 195000
        assert result.method == "SDE"

    def test_arr_multiple_valuation(self):
        engine = ValuationEngine()
        result = engine.arr_valuation(arr=1200000, multiple=4.5)
        assert result.value == 5400000
        assert result.method == "ARR"
