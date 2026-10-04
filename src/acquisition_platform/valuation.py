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
from typing import Any

from acquisition_platform.exceptions import (
    DivisionByZeroError,
    EmptyInputError,
    InvalidRangeError,
    ValidationError,
)
from acquisition_platform.serialization import SerializableMixin


@dataclass
class ValuationResult(SerializableMixin):
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
        if free_cash_flow < 0:
            raise ValidationError(
                f"free_cash_flow must be non-negative, got {free_cash_flow}"
            )
        if growth_rate < 0:
            raise ValidationError(
                f"growth_rate must be non-negative, got {growth_rate}"
            )
        if years <= 0:
            raise ValidationError(f"years must be positive, got {years}")
        if discount_rate < 0:
            raise ValidationError(
                f"discount_rate must be non-negative, got {discount_rate}"
            )
        if terminal_growth < 0:
            raise ValidationError(
                f"terminal_growth must be non-negative, got {terminal_growth}"
            )
        if abs(discount_rate - terminal_growth) < 1e-10:
            raise DivisionByZeroError(
                "discount_rate and terminal_growth cannot be equal "
                f"(both are {discount_rate})"
            )

        pv = 0.0
        for t in range(1, years + 1):
            fcf_t = free_cash_flow * (1 + growth_rate) ** t
            pv += fcf_t / (1 + discount_rate) ** t

        terminal_fcf = free_cash_flow * (1 + growth_rate) ** years * (1 + terminal_growth)
        if terminal_growth > discount_rate:
            # When terminal growth exceeds discount rate, the Gordon Growth Model
            # produces a negative value. Use a large finite horizon approximation.
            terminal_value = terminal_fcf * years / (1 + discount_rate)
        else:
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
        if metric < 0:
            raise ValidationError(f"metric must be non-negative, got {metric}")
        if multiple < 0:
            raise ValidationError(f"multiple must be non-negative, got {multiple}")
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
        if revenue < 0:
            raise ValidationError(f"revenue must be non-negative, got {revenue}")
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

    def value_batch(
        self, financials: list[dict[str, Any]], chunk_size: int = 100
    ) -> list[ValuationResult]:
        """Value a batch of financial records in chunks.

        Each dict in ``financials`` should contain the parameters for one
        valuation method. The method is inferred from the keys present:
        - If ``free_cash_flow`` is present, uses DCF valuation.
        - If ``metric`` is present, uses comparable valuation.
        - If ``sde`` is present, uses SDE valuation.
        - If ``arr`` is present, uses ARR valuation.

        Args:
            financials: List of dicts with valuation parameters.
            chunk_size: Number of records per chunk.

        Returns:
            List of ValuationResult objects.

        Raises:
            EmptyInputError: If financials is empty.
            ValidationError: If chunk_size is not positive or a record
                has unrecognized parameters.
        """
        if not financials:
            raise EmptyInputError("financials list cannot be empty")
        if chunk_size <= 0:
            raise ValidationError(f"chunk_size must be positive, got {chunk_size}")

        all_results: list[ValuationResult] = []
        for i in range(0, len(financials), chunk_size):
            chunk = financials[i : i + chunk_size]
            for record in chunk:
                result = self._value_single(record)
                all_results.append(result)
        return all_results

    def export_valuations(self, valuations: list[ValuationResult], path: str) -> None:
        """Export valuations to a JSON file."""
        from acquisition_platform.data_io import export_to_json
        data = [
            {"value": v.value, "method": v.method, "confidence": v.confidence, "low_estimate": v.low_estimate, "high_estimate": v.high_estimate}
            for v in valuations
        ]
        export_to_json(data, path)

    def import_financials(self, path: str) -> list[dict[str, Any]]:
        """Import financial records from a JSON file."""
        from acquisition_platform.data_io import import_from_json
        result: list[dict[str, Any]] = import_from_json(path)
        return result

    def _value_single(self, record: dict[str, Any]) -> ValuationResult:
        """Value a single financial record, inferring the method from keys."""
        if "free_cash_flow" in record:
            return self.dcf_valuation(
                free_cash_flow=record["free_cash_flow"],
                growth_rate=record.get("growth_rate", 0.0),
                discount_rate=record.get("discount_rate", 0.1),
                terminal_growth=record.get("terminal_growth", 0.02),
                years=record.get("years", 5),
            )
        elif "metric" in record:
            return self.comparable_valuation(
                metric=record["metric"],
                multiple=record.get("multiple", 1.0),
            )
        elif "sde" in record:
            return self.sde_valuation(
                sde=record["sde"],
                multiple=record.get("multiple", 1.0),
            )
        elif "arr" in record:
            return self.arr_valuation(
                arr=record["arr"],
                multiple=record.get("multiple", 1.0),
            )
        else:
            raise ValidationError(
                f"Unrecognized valuation record keys: {list(record.keys())}"
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
        if sde < 0:
            raise ValidationError(f"sde must be non-negative, got {sde}")
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
        if arr < 0:
            raise ValidationError(f"arr must be non-negative, got {arr}")
        value = arr * multiple
        return ValuationResult(
            value=value,
            method="ARR",
            confidence=0.6,
            low_estimate=value * 0.85,
            high_estimate=value * 1.15,
        )