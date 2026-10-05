"""Tests for financial modeling module (defense-focused)."""
import math

import pytest

from acquisition_platform.financial_modeling import (
    DefenseDCF,
    DefenseFinancialModeler,
    LBOModel,
    RealOptions,
)


class TestDefenseDCF:
    """TDD tests for defense DCF valuation."""

    def test_defense_dcf(self):
        modeler = DefenseFinancialModeler()
        model = DefenseDCF(
            free_cash_flows=[100.0, 110.0, 121.0, 133.1, 146.4],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.05,
            recompete_risk=0.03,
        )
        value = modeler.defense_dcf(model)
        assert value > 0
        # Base DCF without adjustments should be positive
        base = sum(
            cf / (1 + model.wacc) ** (i + 1)
            for i, cf in enumerate(model.free_cash_flows)
        )
        assert value > base  # backlog adjustment adds value

    def test_defense_dcf_backlog_increases_value(self):
        modeler = DefenseFinancialModeler()
        base_model = DefenseDCF(
            free_cash_flows=[100.0, 110.0, 121.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.0,
        )
        adj_model = DefenseDCF(
            free_cash_flows=[100.0, 110.0, 121.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.10,
            recompete_risk=0.0,
        )
        assert modeler.defense_dcf(adj_model) > modeler.defense_dcf(base_model)

    def test_defense_dcf_recompete_risk_decreases_value(self):
        modeler = DefenseFinancialModeler()
        low_risk = DefenseDCF(
            free_cash_flows=[100.0, 110.0, 121.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.0,
        )
        high_risk = DefenseDCF(
            free_cash_flows=[100.0, 110.0, 121.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.15,
        )
        assert modeler.defense_dcf(low_risk) > modeler.defense_dcf(high_risk)

    def test_empty_cashflows(self):
        modeler = DefenseFinancialModeler()
        model = DefenseDCF(
            free_cash_flows=[],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.0,
        )
        assert modeler.defense_dcf(model) == 0.0


class TestRealOptions:
    """TDD tests for real options valuation."""

    def test_real_options(self):
        modeler = DefenseFinancialModeler()
        options = RealOptions(
            underlying_value=100.0,
            strike=90.0,
            volatility=0.25,
            time=3.0,
            risk_free_rate=0.04,
        )
        value = modeler.real_options_valuation(options)
        assert value > 0
        # In-the-money call should have positive intrinsic value component
        assert value >= options.underlying_value - options.strike

    def test_real_options_zero_volatility(self):
        modeler = DefenseFinancialModeler()
        options = RealOptions(
            underlying_value=100.0,
            strike=90.0,
            volatility=0.0,
            time=3.0,
            risk_free_rate=0.04,
        )
        value = modeler.real_options_valuation(options)
        # With zero volatility, value = max(S - K*exp(-rT), 0)
        expected = max(
            100.0 - 90.0 * math.exp(-0.04 * 3.0), 0.0
        )
        assert abs(value - expected) < 1e-6

    def test_real_options_higher_volatility_increases_value(self):
        modeler = DefenseFinancialModeler()
        low_vol = RealOptions(
            underlying_value=100.0, strike=100.0,
            volatility=0.10, time=3.0, risk_free_rate=0.04,
        )
        high_vol = RealOptions(
            underlying_value=100.0, strike=100.0,
            volatility=0.50, time=3.0, risk_free_rate=0.04,
        )
        assert modeler.real_options_valuation(high_vol) > modeler.real_options_valuation(low_vol)


class TestLBO:
    """TDD tests for LBO valuation."""

    def test_lbo_valuation(self):
        modeler = DefenseFinancialModeler()
        model = LBOModel(
            purchase_price=500.0,
            debt=350.0,
            equity=150.0,
            exit_multiple=8.0,
            exit_year=5,
        )
        value = modeler.lbo_valuation(model)
        assert value > 0

    def test_lbo_equity_value(self):
        modeler = DefenseFinancialModeler()
        model = LBOModel(
            purchase_price=500.0,
            debt=350.0,
            equity=150.0,
            exit_multiple=8.0,
            exit_year=5,
        )
        # Assume EBITDA = 50, grows at 5% annually
        # Exit EBITDA = 50 * 1.05^5 ≈ 63.8
        # Exit EV = 63.8 * 8 ≈ 510.4
        # Exit equity = 510.4 - 350 = 160.4
        # IRR = (160.4/150)^(1/5) - 1 ≈ 1.35%
        value = modeler.lbo_valuation(model)
        assert isinstance(value, float)

    def test_lbo_higher_exit_multiple_increases_value(self):
        modeler = DefenseFinancialModeler()
        low_mult = LBOModel(
            purchase_price=500.0, debt=350.0, equity=150.0,
            exit_multiple=6.0, exit_year=5,
        )
        high_mult = LBOModel(
            purchase_price=500.0, debt=350.0, equity=150.0,
            exit_multiple=10.0, exit_year=5,
        )
        assert modeler.lbo_valuation(high_mult) > modeler.lbo_valuation(low_mult)


class TestBacklogAdjustment:
    """TDD tests for backlog risk adjustment."""

    def test_backlog_adjustment(self):
        modeler = DefenseFinancialModeler()
        backlog = 200.0
        recompete_probability = 0.20
        adjusted = modeler.backlog_adjustment(backlog, recompete_probability)
        # Expected: 200 * (1 - 0.20) = 160
        assert adjusted == pytest.approx(160.0)

    def test_backlog_adjustment_zero_probability(self):
        modeler = DefenseFinancialModeler()
        adjusted = modeler.backlog_adjustment(200.0, 0.0)
        assert adjusted == pytest.approx(200.0)

    def test_backlog_adjustment_full_probability(self):
        modeler = DefenseFinancialModeler()
        adjusted = modeler.backlog_adjustment(200.0, 1.0)
        assert adjusted == pytest.approx(0.0)


class TestRecompeteRisk:
    """TDD tests for recompete risk factoring."""

    def test_recompete_risk(self):
        modeler = DefenseFinancialModeler()
        # Higher recompete risk should reduce DCF value
        low_risk_model = DefenseDCF(
            free_cash_flows=[100.0, 100.0, 100.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.05,
        )
        high_risk_model = DefenseDCF(
            free_cash_flows=[100.0, 100.0, 100.0],
            wacc=0.10,
            terminal_growth=0.02,
            backlog_adjustment=0.0,
            recompete_risk=0.25,
        )
        assert modeler.defense_dcf(low_risk_model) > modeler.defense_dcf(high_risk_model)


class TestCustomerConcentration:
    """TDD tests for customer concentration risk scoring."""

    def test_customer_concentration(self):
        modeler = DefenseFinancialModeler()
        # Defense contractor with 3 customers: 70%, 20%, 10%
        revenues = [700.0, 200.0, 100.0]
        risk = modeler.customer_concentration_risk(revenues)
        assert risk > 0
        assert risk <= 1.0

    def test_customer_concentration_single_customer(self):
        modeler = DefenseFinancialModeler()
        risk = modeler.customer_concentration_risk([100.0])
        assert risk == pytest.approx(1.0)

    def test_customer_concentration_equal_distribution(self):
        modeler = DefenseFinancialModeler()
        risk = modeler.customer_concentration_risk([25.0, 25.0, 25.0, 25.0])
        assert risk < 0.5  # Low concentration risk


class TestWACC:
    """TDD tests for WACC calculation."""

    def test_wacc_calculation(self):
        modeler = DefenseFinancialModeler()
        wacc = modeler.wacc(
            cost_of_equity=0.12,
            cost_of_debt=0.06,
            tax_rate=0.25,
            equity_weight=0.6,
            debt_weight=0.4,
        )
        # WACC = 0.12*0.6 + 0.06*(1-0.25)*0.4 = 0.072 + 0.018 = 0.09
        assert wacc == pytest.approx(0.09)

    def test_wacc_all_equity(self):
        modeler = DefenseFinancialModeler()
        wacc = modeler.wacc(
            cost_of_equity=0.12,
            cost_of_debt=0.06,
            tax_rate=0.25,
            equity_weight=1.0,
            debt_weight=0.0,
        )
        assert wacc == pytest.approx(0.12)

    def test_wacc_all_debt(self):
        modeler = DefenseFinancialModeler()
        wacc = modeler.wacc(
            cost_of_equity=0.12,
            cost_of_debt=0.06,
            tax_rate=0.25,
            equity_weight=0.0,
            debt_weight=1.0,
        )
        assert wacc == pytest.approx(0.045)  # 0.06 * (1 - 0.25)


class TestSensitivityAnalysis:
    """TDD tests for sensitivity analysis."""

    def test_sensitivity_analysis(self):
        modeler = DefenseFinancialModeler()
        base_value = 1000.0
        variables = {
            "wacc": [0.08, 0.10, 0.12],
            "growth": [0.01, 0.02, 0.03],
        }
        result = modeler.sensitivity_analysis(base_value, variables)
        assert isinstance(result, dict)
        assert "wacc" in result
        assert "growth" in result
        assert len(result["wacc"]) == 3
        assert len(result["growth"]) == 3

    def test_sensitivity_analysis_higher_wacc_lowers_value(self):
        modeler = DefenseFinancialModeler()
        base_value = 1000.0
        variables = {"wacc": [0.08, 0.10, 0.12]}
        result = modeler.sensitivity_analysis(base_value, variables)
        values = list(result["wacc"].values())
        assert values[0] > values[1] > values[2]


class TestScenarioAnalysis:
    """TDD tests for scenario analysis."""

    def test_scenario_analysis(self):
        modeler = DefenseFinancialModeler()
        scenarios = {
            "bear": {"revenue_growth": -0.05, "margin": 0.08, "multiple": 5.0},
            "base": {"revenue_growth": 0.03, "margin": 0.12, "multiple": 7.0},
            "bull": {"revenue_growth": 0.08, "margin": 0.16, "multiple": 10.0},
        }
        result = modeler.scenario_analysis(scenarios)
        assert isinstance(result, dict)
        assert "bear" in result
        assert "base" in result
        assert "bull" in result
        assert result["bull"] > result["base"] > result["bear"]

    def test_scenario_analysis_returns_values(self):
        modeler = DefenseFinancialModeler()
        scenarios = {
            "low": {"revenue_growth": 0.0, "margin": 0.10, "multiple": 5.0},
            "high": {"revenue_growth": 0.10, "margin": 0.20, "multiple": 12.0},
        }
        result = modeler.scenario_analysis(scenarios)
        for value in result.values():
            assert value > 0
