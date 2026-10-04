"""Valuation engine for acquisition target pricing.

This module implements multiple valuation methodologies used in M&A
analysis. The underlying problem of determining a fair acquisition price
is PPAD-hard (Polynomial-time Parity Arguments on Directed graphs) — it
belongs to the class of total search problems that lie between P and NP,
encompassing Nash equilibrium computation and Arrow-Debreu market
equilibrium. Exact solutions require exponential time in the worst case,
so practitioners rely on approximation methods like DCF, comparable
company analysis, and ensemble approaches that combine multiple signals.
"""

from dataclasses import dataclass


@dataclass
class ValuationResult:
    """Result of a valuation calculation.

    Attributes:
        value: The estimated valuation.
        method: Name of the valuation method used.
        confidence: Confidence score in [0, 1].
        low_estimate: Lower bound of the valuation range.
        high_estimate: Upper bound of the valuation range.
    """

    value: float
    method: str
    confidence: float
    low_estimate: float
    high_estimate: float


class ValuationEngine:
    """Engine for computing valuations using multiple methodologies."""

    def dcf_valuation(
        self,
        free_cash_flow: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth: float,
        years: int,
    ) -> ValuationResult:
        """Discounted Cash Flow valuation.

        Sums the present value of projected free cash flows over a
        forecast period, then adds the discounted terminal value
        computed via the Gordon Growth Model.

        Args:
            free_cash_flow: Base-year free cash flow.
            growth_rate: Annual FCF growth rate during forecast period.
            discount_rate: Required rate of return (WACC).
            terminal_growth: Perpetual growth rate beyond forecast.
            years: Number of explicit forecast years.

        Returns:
            ValuationResult with method "DCF".
        """
        pv = 0.0
        for t in range(1, years + 1):
            fcf_t = free_cash_flow * (1 + growth_rate) ** t
            pv += fcf_t / (1 + discount_rate) ** t

        terminal_fcf = free_cash_flow * (1 + growth_rate) ** years * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / (1 + discount_rate) ** years

        value = pv + pv_terminal
        return ValuationResult(
            value=value,
            method="DCF",
            confidence=0.7,
            low_estimate=value * 0.85,
            high_estimate=value * 1.15,
        )

    def comparable_valuation(self, metric: float, multiple: float) -> ValuationResult:
        """Comparable company (comps) valuation.

        Multiplies a financial metric (revenue, EBITDA, etc.) by a
        market multiple derived from comparable public companies.

        Args:
            metric: Financial metric (e.g., revenue, EBITDA).
            multiple: Valuation multiple (e.g., EV/Revenue).

        Returns:
            ValuationResult with method "Comps".
        """
        value = metric * multiple
        return ValuationResult(
            value=value,
            method="Comps",
            confidence=0.6,
            low_estimate=value * 0.85,
            high_estimate=value * 1.15,
        )

    def ensemble_valuation(
        self,
        free_cash_flow: float,
        revenue: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth: float,
        revenue_multiple: float,
        years: int,
    ) -> ValuationResult:
        """Ensemble valuation combining DCF and comparable methods.

        Averages the DCF and Comps valuations. Confidence is derived
        from the degree of agreement between the two methods.

        Args:
            free_cash_flow: Base-year free cash flow for DCF.
            revenue: Annual revenue for comps.
            growth_rate: Annual FCF growth rate.
            discount_rate: Discount rate (WACC).
            terminal_growth: Perpetual growth rate.
            revenue_multiple: EV/Revenue multiple.
            years: Forecast period length.

        Returns:
            ValuationResult with method "Ensemble".
        """
        dcf_result = self.dcf_valuation(
            free_cash_flow=free_cash_flow,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            years=years,
        )
        comps_result = self.comparable_valuation(
            metric=revenue,
            multiple=revenue_multiple,
        )

        methods = [dcf_result.value, comps_result.value]
        value = sum(methods) / len(methods)

        low_estimate = min(methods) * 0.85
        high_estimate = max(methods) * 1.15

        confidence = 1 - (high_estimate - low_estimate) / (2 * value)
        confidence = max(0.0, min(1.0, confidence))

        return ValuationResult(
            value=value,
            method="Ensemble",
            confidence=confidence,
            low_estimate=low_estimate,
            high_estimate=high_estimate,
        )

    def sde_valuation(self, sde: float, multiple: float) -> ValuationResult:
        """Seller's Discretionary Earnings valuation.

        Multiplies SDE (the true economic benefit to an owner-operator)
        by a market multiple, commonly used for small business acquisitions.

        Args:
            sde: Seller's Discretionary Earnings.
            multiple: SDE multiple.

        Returns:
            ValuationResult with method "SDE".
        """
        value = sde * multiple
        return ValuationResult(
            value=value,
            method="SDE",
            confidence=0.6,
            low_estimate=value * 0.85,
            high_estimate=value * 1.15,
        )

    def arr_valuation(self, arr: float, multiple: float) -> ValuationResult:
        """Annual Recurring Revenue valuation.

        Multiplies ARR by a revenue multiple, commonly used for SaaS
        and subscription business acquisitions.

        Args:
            arr: Annual Recurring Revenue.
            multiple: ARR multiple.

        Returns:
            ValuationResult with method "ARR".
        """
        value = arr * multiple
        return ValuationResult(
            value=value,
            method="ARR",
            confidence=0.6,
            low_estimate=value * 0.85,
            high_estimate=value * 1.15,
        )
