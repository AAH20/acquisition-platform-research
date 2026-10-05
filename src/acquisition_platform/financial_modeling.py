"""Financial modeling module for defense acquisition analysis.

This module implements defense-specific financial modeling tools including
DCF with backlog and recompete adjustments, real options valuation,
LBO modeling, customer concentration risk scoring, WACC calculation,
sensitivity analysis, and scenario analysis.
"""

import math
from dataclasses import dataclass

from acquisition_platform.exceptions import (
    DivisionByZeroError,
    EmptyInputError,
    InvalidRangeError,
    ValidationError,
)


@dataclass
class DefenseDCF:
    """Defense DCF model with backlog and recompete adjustments.

    Attributes:
        free_cash_flows: Projected free cash flows for each forecast year.
        wacc: Weighted average cost of capital (discount rate).
        terminal_growth: Perpetual growth rate beyond forecast period.
        backlog_adjustment: Value uplift from contracted backlog (0-1).
        recompete_risk: Probability-weighted revenue loss from recompetes (0-1).
    """

    free_cash_flows: list[float]
    wacc: float
    terminal_growth: float
    backlog_adjustment: float
    recompete_risk: float


@dataclass
class RealOptions:
    """Real options valuation parameters (Black-Scholes).

    Attributes:
        underlying_value: Current value of the underlying asset (S).
        strike: Exercise price of the option (K).
        volatility: Annualized volatility of returns (sigma).
        time: Time to expiration in years (T).
        risk_free_rate: Risk-free interest rate (r).
    """

    underlying_value: float
    strike: float
    volatility: float
    time: float
    risk_free_rate: float


@dataclass
class LBOModel:
    """Leveraged Buyout model parameters.

    Attributes:
        purchase_price: Total enterprise value at entry.
        debt: Debt financing amount.
        equity: Equity financing amount.
        exit_multiple: EV/EBITDA multiple at exit.
        exit_year: Year of exit.
    """

    purchase_price: float
    debt: float
    equity: float
    exit_multiple: float
    exit_year: int


class DefenseFinancialModeler:
    """Financial modeler for defense acquisition analysis."""

    def defense_dcf(self, model: DefenseDCF) -> float:
        """Defense DCF valuation with backlog and recompete adjustments.

        Computes PV of explicit FCFs plus terminal value, then applies
        backlog adjustment (uplift) and recompete risk (haircut).

        Args:
            model: DefenseDCF with all parameters.

        Returns:
            Adjusted DCF valuation. Returns 0.0 for empty cashflows.

        Raises:
            ValidationError: If wacc or terminal_growth is negative.
            DivisionByZeroError: If wacc equals terminal_growth.
        """
        if not model.free_cash_flows:
            return 0.0
        if model.wacc < 0:
            raise ValidationError(f"wacc must be non-negative, got {model.wacc}")
        if model.terminal_growth < 0:
            raise ValidationError(
                f"terminal_growth must be non-negative, got {model.terminal_growth}"
            )
        if abs(model.wacc - model.terminal_growth) < 1e-10:
            raise DivisionByZeroError(
                "wacc and terminal_growth cannot be equal "
                f"(both are {model.wacc})"
            )
        if not 0 <= model.backlog_adjustment <= 1:
            raise InvalidRangeError(
                f"backlog_adjustment must be in [0, 1], got {model.backlog_adjustment}"
            )
        if not 0 <= model.recompete_risk <= 1:
            raise InvalidRangeError(
                f"recompete_risk must be in [0, 1], got {model.recompete_risk}"
            )

        # PV of explicit forecast period
        pv_explicit = sum(
            cf / (1 + model.wacc) ** (i + 1)
            for i, cf in enumerate(model.free_cash_flows)
        )

        # Terminal value via Gordon Growth Model
        last_fcf = model.free_cash_flows[-1]
        terminal_fcf = last_fcf * (1 + model.terminal_growth)
        terminal_value = terminal_fcf / (model.wacc - model.terminal_growth)
        pv_terminal = terminal_value / (1 + model.wacc) ** len(model.free_cash_flows)

        base_value = pv_explicit + pv_terminal

        # Apply backlog adjustment (uplift) and recompete risk (haircut)
        adjusted_value = base_value * (1 + model.backlog_adjustment)
        adjusted_value *= (1 - model.recompete_risk)

        return adjusted_value

    def real_options_valuation(self, options: RealOptions) -> float:
        """Real options valuation using Black-Scholes approximation.

        Args:
            options: RealOptions with all parameters.

        Returns:
            Call option value.

        Raises:
            ValidationError: If underlying_value, strike, or time is negative.
        """
        if options.underlying_value < 0:
            raise ValidationError(
                f"underlying_value must be non-negative, got {options.underlying_value}"
            )
        if options.strike < 0:
            raise ValidationError(f"strike must be non-negative, got {options.strike}")
        if options.time < 0:
            raise ValidationError(f"time must be non-negative, got {options.time}")
        if options.volatility < 0:
            raise ValidationError(
                f"volatility must be non-negative, got {options.volatility}"
            )

        S = options.underlying_value
        K = options.strike
        sigma = options.volatility
        T = options.time
        r = options.risk_free_rate

        if sigma == 0 or T == 0:
            # No time value — intrinsic value only
            return max(S - K * math.exp(-r * T), 0.0)

        d1 = (
            math.log(S / K)
            + (r + 0.5 * sigma ** 2) * T
        ) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Cumulative normal distribution approximation
        Nd1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
        Nd2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))

        call_value = S * Nd1 - K * math.exp(-r * T) * Nd2
        return max(call_value, 0.0)

    def lbo_valuation(self, model: LBOModel) -> float:
        """LBO valuation computing equity value at exit.

        Assumes EBITDA = purchase_price / 8.0 (typical defense entry multiple),
        5% annual EBITDA growth, and computes exit equity value.

        Args:
            model: LBOModel with all parameters.

        Returns:
            Equity value at exit.

        Raises:
            ValidationError: If purchase_price, debt, equity, or exit_multiple
                is negative, or exit_year is not positive.
        """
        if model.purchase_price < 0:
            raise ValidationError(
                f"purchase_price must be non-negative, got {model.purchase_price}"
            )
        if model.debt < 0:
            raise ValidationError(f"debt must be non-negative, got {model.debt}")
        if model.equity < 0:
            raise ValidationError(f"equity must be non-negative, got {model.equity}")
        if model.exit_multiple < 0:
            raise ValidationError(
                f"exit_multiple must be non-negative, got {model.exit_multiple}"
            )
        if model.exit_year <= 0:
            raise ValidationError(f"exit_year must be positive, got {model.exit_year}")

        # Derive entry EBITDA from purchase price (8x entry multiple assumption)
        entry_multiple = 8.0
        entry_ebitda = model.purchase_price / entry_multiple

        # Project EBITDA at exit (5% annual growth)
        growth_rate = 0.05
        exit_ebitda = entry_ebitda * (1 + growth_rate) ** model.exit_year

        # Exit enterprise value and equity value
        exit_ev = exit_ebitda * model.exit_multiple
        exit_equity = exit_ev - model.debt

        return max(exit_equity, 0.0)

    def backlog_adjustment(self, backlog: float, recompete_probability: float) -> float:
        """Compute risk-adjusted backlog value.

        Args:
            backlog: Total contracted backlog value.
            recompete_probability: Probability of losing recompete (0-1).

        Returns:
            Risk-adjusted backlog value.

        Raises:
            ValidationError: If backlog is negative.
            InvalidRangeError: If recompete_probability is outside [0, 1].
        """
        if backlog < 0:
            raise ValidationError(f"backlog must be non-negative, got {backlog}")
        if not 0 <= recompete_probability <= 1:
            raise InvalidRangeError(
                f"recompete_probability must be in [0, 1], got {recompete_probability}"
            )
        return backlog * (1 - recompete_probability)

    def customer_concentration_risk(self, revenues: list[float]) -> float:
        """Compute customer concentration risk using HHI.

        Uses the Herfindahl-Hirschman Index (sum of squared market shares)
        as a concentration risk score. Returns 1.0 for a single customer,
        lower values for more diversified revenue.

        Args:
            revenues: List of revenue per customer.

        Returns:
            Concentration risk score in [0, 1].

        Raises:
            EmptyInputError: If revenues is empty.
            ValidationError: If any revenue is negative.
        """
        if not revenues:
            raise EmptyInputError("revenues list cannot be empty")
        if any(r < 0 for r in revenues):
            raise ValidationError("all revenues must be non-negative")

        total = sum(revenues)
        if total == 0:
            return 0.0

        shares = [r / total for r in revenues]
        hhi = sum(s ** 2 for s in shares)
        return hhi

    def wacc(
        self,
        cost_of_equity: float,
        cost_of_debt: float,
        tax_rate: float,
        equity_weight: float,
        debt_weight: float,
    ) -> float:
        """Calculate Weighted Average Cost of Capital.

        WACC = E/V * Re + D/V * Rd * (1 - Tc)

        Args:
            cost_of_equity: Required return on equity (Re).
            cost_of_debt: Cost of debt (Rd).
            tax_rate: Corporate tax rate (Tc).
            equity_weight: Proportion of equity financing (E/V).
            debt_weight: Proportion of debt financing (D/V).

        Returns:
            WACC as a decimal.

        Raises:
            ValidationError: If any input is negative.
            InvalidRangeError: If weights don't sum to 1.0 or tax_rate > 1.
        """
        if cost_of_equity < 0:
            raise ValidationError(
                f"cost_of_equity must be non-negative, got {cost_of_equity}"
            )
        if cost_of_debt < 0:
            raise ValidationError(f"cost_of_debt must be non-negative, got {cost_of_debt}")
        if tax_rate < 0 or tax_rate > 1:
            raise InvalidRangeError(f"tax_rate must be in [0, 1], got {tax_rate}")
        if equity_weight < 0 or debt_weight < 0:
            raise ValidationError("weights must be non-negative")
        if abs(equity_weight + debt_weight - 1.0) > 1e-6:
            raise ValidationError(
                f"equity_weight + debt_weight must equal 1.0, "
                f"got {equity_weight + debt_weight}"
            )

        return (
            equity_weight * cost_of_equity
            + debt_weight * cost_of_debt * (1 - tax_rate)
        )

    def sensitivity_analysis(
        self, base_value: float, variables: dict[str, list[float]]
    ) -> dict[str, dict[float, float]]:
        """Generate sensitivity table for key variables.

        For each variable and each value, computes the adjusted valuation.
        - wacc: value scales inversely (base_wacc / new_wacc)
        - growth: value scales with (1 + new_growth) / (1 + base_growth)
        - multiple: value scales linearly with new_multiple / base_multiple

        Args:
            base_value: Base case valuation.
            variables: Dict mapping variable name to list of test values.

        Returns:
            Dict mapping variable name to dict of {input_value: output_value}.

        Raises:
            ValidationError: If base_value is negative.
            EmptyInputError: If variables is empty.
        """
        if base_value < 0:
            raise ValidationError(f"base_value must be non-negative, got {base_value}")
        if not variables:
            raise EmptyInputError("variables dict cannot be empty")

        result: dict[str, dict[float, float]] = {}

        for var_name, values in variables.items():
            if not values:
                raise EmptyInputError(f"values for {var_name} cannot be empty")

            result[var_name] = {}
            for val in values:
                if var_name == "wacc":
                    # Higher WACC → lower value (inverse relationship)
                    base_wacc = 0.10
                    if val <= 0:
                        result[var_name][val] = base_value
                    else:
                        result[var_name][val] = base_value * (base_wacc / val)
                elif var_name == "growth":
                    # Higher growth → higher value
                    base_growth = 0.02
                    result[var_name][val] = base_value * (1 + val) / (1 + base_growth)
                elif var_name == "multiple":
                    # Higher multiple → higher value (linear)
                    base_multiple = 8.0
                    if val < 0:
                        raise ValidationError(
                            f"multiple value must be non-negative, got {val}"
                        )
                    result[var_name][val] = base_value * val / base_multiple
                else:
                    # Generic: proportional scaling
                    result[var_name][val] = base_value * val

        return result

    def scenario_analysis(self, scenarios: dict[str, dict[str, float]]) -> dict[str, float]:
        """Compare multiple scenarios (bear/base/bull).

        Computes valuation for each scenario using:
        Value = Base_Revenue * (1 + growth)^years * margin * multiple

        Args:
            scenarios: Dict mapping scenario name to dict with keys:
                revenue_growth, margin, multiple.

        Returns:
            Dict mapping scenario name to computed valuation.

        Raises:
            EmptyInputError: If scenarios is empty.
            ValidationError: If any scenario value is negative.
        """
        if not scenarios:
            raise EmptyInputError("scenarios dict cannot be empty")

        base_revenue = 1000.0
        years = 5

        result: dict[str, float] = {}
        for name, params in scenarios.items():
            growth = params.get("revenue_growth", 0.0)
            margin = params.get("margin", 0.10)
            multiple = params.get("multiple", 7.0)

            if margin < 0:
                raise ValidationError(
                    f"margin must be non-negative for scenario {name}, got {margin}"
                )
            if multiple < 0:
                raise ValidationError(
                    f"multiple must be non-negative for scenario {name}, got {multiple}"
                )

            exit_revenue = base_revenue * (1 + growth) ** years
            exit_ebitda = exit_revenue * margin
            value = exit_ebitda * multiple
            result[name] = value

        return result
