"""Deal structuring module for M&A transactions.

This module models the structural components of an acquisition deal:
earnouts, contingent value rights (CVRs), escrow arrangements,
indemnification caps, cross-border adjustments, regulatory holdbacks,
and synergy valuations. Each component is valued using
probability-weighted expected payout methodology, consistent with
how risk-adjusted consideration is computed in practice.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acquisition_platform.exceptions import InvalidRangeError, ValidationError
from acquisition_platform.observability import get_logger, log_execution_time
from acquisition_platform.serialization import SerializableMixin

logger = get_logger(__name__)


@dataclass
class Earnout(SerializableMixin):
    """Earnout provision tied to post-closing performance targets.

    Attributes:
        target_revenue: Revenue target the seller must achieve.
        target_profit: Profit target the seller must achieve.
        max_payout: Maximum payout if all targets are met.
        probability: Probability of achieving the targets, in [0, 1].
    """

    target_revenue: float = 0.0
    target_profit: float = 0.0
    max_payout: float = 0.0
    probability: float = 0.0


@dataclass
class CVR(SerializableMixin):
    """Contingent Value Right tied to a specific milestone.

    Attributes:
        milestone: Description of the milestone (e.g. "FDA approval").
        payout: Payout if the milestone is achieved.
        probability: Probability of achieving the milestone, in [0, 1].
    """

    milestone: str = ""
    payout: float = 0.0
    probability: float = 0.0


@dataclass
class DealStructure(SerializableMixin):
    """Complete structural terms of an acquisition deal.

    Attributes:
        purchase_price: Base purchase price.
        earnout: Earnout provision.
        cvr: List of contingent value rights.
        escrow: Escrow amount held back for adjustments.
        indemnification_cap: Maximum indemnification liability.
    """

    purchase_price: float = 0.0
    earnout: Earnout = field(default_factory=Earnout)
    cvr: list[CVR] = field(default_factory=list)
    escrow: float = 0.0
    indemnification_cap: float = 0.0


class DealStructurer:
    """Engine for valuing and adjusting deal structure components."""

    # Escrow rate as a fraction of purchase price at risk_score = 1.0.
    _ESCROW_RATE = 0.25
    # Indemnification cap rate as a fraction of purchase price at risk_score = 1.0.
    _INDEMNIFICATION_RATE = 0.40
    # Regulatory holdback rate as a fraction of purchase price at regulatory_risk = 1.0.
    _REGULATORY_HOLDBACK_RATE = 0.15

    @log_execution_time(logger)
    def value_earnout(self, earnout: Earnout) -> float:
        """Value an earnout as its probability-weighted maximum payout.

        Args:
            earnout: The earnout provision to value.

        Returns:
            The expected value of the earnout.

        Raises:
            ValidationError: If any earnout field is negative.
            InvalidRangeError: If probability is outside [0, 1].
        """
        self._validate_earnout(earnout)
        return earnout.max_payout * earnout.probability

    @log_execution_time(logger)
    def value_cvr(self, cvr: list[CVR]) -> float:
        """Value a set of contingent value rights.

        Args:
            cvr: List of CVRs to value.

        Returns:
            The sum of probability-weighted payouts across all CVRs.

        Raises:
            ValidationError: If any CVR payout is negative.
            InvalidRangeError: If any probability is outside [0, 1].
        """
        total = 0.0
        for right in cvr:
            if right.payout < 0:
                raise ValidationError("CVR payout must be non-negative")
            if not 0.0 <= right.probability <= 1.0:
                raise InvalidRangeError("CVR probability must be in [0, 1]")
            total += right.payout * right.probability
        return total

    @log_execution_time(logger)
    def calculate_escrow(self, purchase_price: float, risk_score: float) -> float:
        """Calculate the escrow amount for a deal.

        The escrow is a fixed percentage of the purchase price scaled by
        the risk score of the target.

        Args:
            purchase_price: The base purchase price.
            risk_score: Risk score in [0, 1]; higher means more escrow.

        Returns:
            The escrow amount.

        Raises:
            ValidationError: If purchase_price is negative.
            InvalidRangeError: If risk_score is outside [0, 1].
        """
        if purchase_price < 0:
            raise ValidationError("Purchase price must be non-negative")
        if not 0.0 <= risk_score <= 1.0:
            raise InvalidRangeError("Risk score must be in [0, 1]")
        return purchase_price * self._ESCROW_RATE * risk_score

    @log_execution_time(logger)
    def set_indemnification_cap(self, purchase_price: float, risk_score: float) -> float:
        """Set the indemnification cap for a deal.

        The cap is a fixed percentage of the purchase price scaled by
        the risk score of the target.

        Args:
            purchase_price: The base purchase price.
            risk_score: Risk score in [0, 1]; higher means a higher cap.

        Returns:
            The indemnification cap.

        Raises:
            ValidationError: If purchase_price is negative.
            InvalidRangeError: If risk_score is outside [0, 1].
        """
        if purchase_price < 0:
            raise ValidationError("Purchase price must be non-negative")
        if not 0.0 <= risk_score <= 1.0:
            raise InvalidRangeError("Risk score must be in [0, 1]")
        return purchase_price * self._INDEMNIFICATION_RATE * risk_score

    @log_execution_time(logger)
    def cross_border_adjustment(
        self, structure: DealStructure, country_risk: float
    ) -> DealStructure:
        """Adjust a deal structure for cross-border country risk.

        Escrow and indemnification cap are scaled up by the country
        risk premium; the purchase price is unchanged.

        Args:
            structure: The deal structure to adjust.
            country_risk: Country risk premium in [0, 1].

        Returns:
            A new DealStructure with adjusted escrow and indemnification cap.

        Raises:
            InvalidRangeError: If country_risk is outside [0, 1].
        """
        if not 0.0 <= country_risk <= 1.0:
            raise InvalidRangeError("Country risk must be in [0, 1]")
        multiplier = 1.0 + country_risk
        return DealStructure(
            purchase_price=structure.purchase_price,
            earnout=structure.earnout,
            cvr=structure.cvr,
            escrow=structure.escrow * multiplier,
            indemnification_cap=structure.indemnification_cap * multiplier,
        )

    @log_execution_time(logger)
    def regulatory_holdback(self, purchase_price: float, regulatory_risk: float) -> float:
        """Calculate the regulatory holdback amount.

        A portion of the purchase price held back until regulatory
        approvals are obtained, scaled by regulatory risk.

        Args:
            purchase_price: The base purchase price.
            regulatory_risk: Regulatory risk in [0, 1].

        Returns:
            The regulatory holdback amount.

        Raises:
            ValidationError: If purchase_price is negative.
            InvalidRangeError: If regulatory_risk is outside [0, 1].
        """
        if purchase_price < 0:
            raise ValidationError("Purchase price must be non-negative")
        if not 0.0 <= regulatory_risk <= 1.0:
            raise InvalidRangeError("Regulatory risk must be in [0, 1]")
        return purchase_price * self._REGULATORY_HOLDBACK_RATE * regulatory_risk

    @log_execution_time(logger)
    def probability_weighted_earnout(self, earnout: Earnout) -> float:
        """Compute the probability-weighted value of an earnout.

        Args:
            earnout: The earnout provision to value.

        Returns:
            The probability-weighted expected payout.

        Raises:
            ValidationError: If any earnout field is negative.
            InvalidRangeError: If probability is outside [0, 1].
        """
        return self.value_earnout(earnout)

    @log_execution_time(logger)
    def value_synergies(
        self,
        revenue_synergies: float,
        cost_synergies: float,
        discount_rate: float,
    ) -> float:
        """Value synergies as a perpetuity of after-tax annual benefits.

        Synergies are capitalized as a growing perpetuity with zero
        growth: total annual synergies divided by the discount rate.

        Args:
            revenue_synergies: Annual revenue synergies.
            cost_synergies: Annual cost synergies.
            discount_rate: Discount rate in (0, 1].

        Returns:
            The capitalized value of the synergies.

        Raises:
            ValidationError: If any synergy input is negative.
            InvalidRangeError: If discount_rate is outside (0, 1].
        """
        if revenue_synergies < 0 or cost_synergies < 0:
            raise ValidationError("Synergies must be non-negative")
        if not 0.0 < discount_rate <= 1.0:
            raise InvalidRangeError("Discount rate must be in (0, 1]")
        return (revenue_synergies + cost_synergies) / discount_rate

    @log_execution_time(logger)
    def generate_structure_report(self, structure: DealStructure) -> dict[str, Any]:
        """Generate a summary report of a deal structure.

        Args:
            structure: The deal structure to report on.

        Returns:
            A dictionary with valued components and total consideration.
        """
        earnout_value = self.value_earnout(structure.earnout)
        cvr_value = self.value_cvr(structure.cvr)
        return {
            "purchase_price": structure.purchase_price,
            "earnout_value": earnout_value,
            "cvr_value": cvr_value,
            "escrow": structure.escrow,
            "indemnification_cap": structure.indemnification_cap,
            "total_consideration": structure.purchase_price + earnout_value + cvr_value,
        }

    @staticmethod
    def _validate_earnout(earnout: Earnout) -> None:
        """Validate earnout fields.

        Args:
            earnout: The earnout to validate.

        Raises:
            ValidationError: If any field is negative.
            InvalidRangeError: If probability is outside [0, 1].
        """
        if (
            earnout.target_revenue < 0
            or earnout.target_profit < 0
            or earnout.max_payout < 0
        ):
            raise ValidationError("Earnout fields must be non-negative")
        if not 0.0 <= earnout.probability <= 1.0:
            raise InvalidRangeError("Earnout probability must be in [0, 1]")
