"""Cross-Border Deal Optimizer.

Handles regulatory filing coordination, tax optimization, currency hedging,
and integration planning for cross-border M&A transactions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


@dataclass
class Jurisdiction(SerializableMixin):
    """A country or regulatory jurisdiction involved in a cross-border deal."""

    code: str
    name: str
    regulatory_body: str
    tax_rate: float


@dataclass
class RegulatoryFiling(SerializableMixin):
    """A required regulatory filing in a specific jurisdiction."""

    jurisdiction: str
    filing_type: str
    deadline: float
    dependencies: list[str] = field(default_factory=list)


@dataclass
class CrossBorderDeal(SerializableMixin):
    """A cross-border acquisition deal spanning multiple jurisdictions."""

    jurisdictions: list[Jurisdiction]
    deal_value: float
    deal_type: str


@dataclass
class CrossBorderResult(SerializableMixin):
    """Result of cross-border deal optimization."""

    filings: list[RegulatoryFiling] = field(default_factory=list)
    total_tax: float = 0.0
    hedging_cost: float = 0.0
    integration_timeline: float = 0.0
    risk_score: float = 0.0


class CrossBorderOptimizer:
    """Optimizer for cross-border M&A transactions.

    Coordinates regulatory filings across jurisdictions, minimizes tax
    burden through treaty optimization, hedges FX risk, and plans
    integration timelines.
    """

    # Base filing deadlines (in days from deal announcement)
    _FILING_DEADLINES: dict[str, float] = {
        "fdi_screening": 30.0,
        "antitrust_notification": 45.0,
        "foreign_investment_review": 60.0,
        "securities_filing": 90.0,
        "tax_registration": 15.0,
    }

    # Base integration time (months) and per-jurisdiction increment
    _BASE_INTEGRATION_MONTHS: float = 6.0
    _PER_JURISDICTION_MONTHS: float = 3.0

    # Hedging cost as fraction of deal value per jurisdiction pair
    _HEDGE_COST_RATE: float = 0.005  # 0.5%

    @log_execution_time(logger)
    def optimize(self, deal: CrossBorderDeal) -> CrossBorderResult:
        """Run full cross-border optimization.

        Args:
            deal: The cross-border deal to optimize.

        Returns:
            CrossBorderResult with filings, tax, hedging, timeline, and risk.

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        filings = self.coordinate_regulatory(deal)
        total_tax = self.optimize_tax(deal)
        hedging_cost = self.hedge_currency(deal)
        integration_timeline = self.plan_integration(deal)
        risk_score = self._compute_risk_score(deal)

        return CrossBorderResult(
            filings=filings,
            total_tax=total_tax,
            hedging_cost=hedging_cost,
            integration_timeline=integration_timeline,
            risk_score=risk_score,
        )

    @log_execution_time(logger)
    def coordinate_regulatory(self, deal: CrossBorderDeal) -> list[RegulatoryFiling]:
        """Generate and sequence all required regulatory filings.

        Filings are sorted by deadline. Dependencies are resolved so that
        prerequisite filings always appear before dependent filings.

        Args:
            deal: The cross-border deal.

        Returns:
            Ordered list of RegulatoryFiling objects.
        """
        if not deal.jurisdictions:
            return []

        filings: list[RegulatoryFiling] = []
        for jurisdiction in deal.jurisdictions:
            filings.extend(self._generate_jurisdiction_filings(jurisdiction))

        # Sort by deadline, then by filing_type for deterministic ordering
        filings.sort(key=lambda f: (f.deadline, f.filing_type))
        return filings

    @log_execution_time(logger)
    def optimize_tax(self, deal: CrossBorderDeal) -> float:
        """Minimize tax burden using treaty optimization.

        Uses the most favorable tax rate among jurisdictions (treaty routing)
        as the effective rate, which is always <= the maximum single rate
        and strictly less than the naive sum of all rates.

        Args:
            deal: The cross-border deal.

        Returns:
            Optimized total tax amount.
        """
        if not deal.jurisdictions:
            return 0.0

        # Treaty optimization: route through the lowest-tax jurisdiction
        min_rate = min(j.tax_rate for j in deal.jurisdictions)
        return min_rate * deal.deal_value

    @log_execution_time(logger)
    def hedge_currency(self, deal: CrossBorderDeal) -> float:
        """Calculate currency hedging cost for FX risk.

        Cost scales with the number of jurisdiction pairs (currency pairs).

        Args:
            deal: The cross-border deal.

        Returns:
            Total hedging cost.
        """
        if not deal.jurisdictions:
            return 0.0

        n = len(deal.jurisdictions)
        # Number of currency pairs: n * (n - 1) / 2, plus a base hedge per jurisdiction
        num_pairs = n * (n - 1) // 2
        base_hedge = n * self._HEDGE_COST_RATE * deal.deal_value
        pair_hedge = num_pairs * self._HEDGE_COST_RATE * deal.deal_value
        return base_hedge + pair_hedge

    @log_execution_time(logger)
    def plan_integration(self, deal: CrossBorderDeal) -> float:
        """Estimate integration timeline in months.

        Timeline scales with the number of jurisdictions involved.

        Args:
            deal: The cross-border deal.

        Returns:
            Estimated integration timeline in months.
        """
        if not deal.jurisdictions:
            return 0.0

        n = len(deal.jurisdictions)
        return self._BASE_INTEGRATION_MONTHS + n * self._PER_JURISDICTION_MONTHS

    def _generate_jurisdiction_filings(
        self, jurisdiction: Jurisdiction
    ) -> list[RegulatoryFiling]:
        """Generate all required filings for a single jurisdiction."""
        code = jurisdiction.code
        return [
            RegulatoryFiling(
                jurisdiction=code,
                filing_type="tax_registration",
                deadline=self._FILING_DEADLINES["tax_registration"],
                dependencies=[],
            ),
            RegulatoryFiling(
                jurisdiction=code,
                filing_type="fdi_screening",
                deadline=self._FILING_DEADLINES["fdi_screening"],
                dependencies=[],
            ),
            RegulatoryFiling(
                jurisdiction=code,
                filing_type="antitrust_notification",
                deadline=self._FILING_DEADLINES["antitrust_notification"],
                dependencies=["fdi_screening"],
            ),
            RegulatoryFiling(
                jurisdiction=code,
                filing_type="foreign_investment_review",
                deadline=self._FILING_DEADLINES["foreign_investment_review"],
                dependencies=["fdi_screening", "antitrust_notification"],
            ),
            RegulatoryFiling(
                jurisdiction=code,
                filing_type="securities_filing",
                deadline=self._FILING_DEADLINES["securities_filing"],
                dependencies=["foreign_investment_review"],
            ),
        ]

    def _compute_risk_score(self, deal: CrossBorderDeal) -> float:
        """Compute a normalized risk score in [0, 1].

        Risk increases with number of jurisdictions, average tax rate,
        and deal value.
        """
        if not deal.jurisdictions:
            return 0.0

        n = len(deal.jurisdictions)
        avg_tax_rate = sum(j.tax_rate for j in deal.jurisdictions) / n

        # Jurisdiction count risk: saturates at 10 jurisdictions
        jurisdiction_risk = min(n / 10.0, 1.0)

        # Tax rate risk: normalize against a 50% max rate
        tax_risk = avg_tax_rate / 0.5

        # Deal value risk: log-scale, saturates at $10B
        import math
        value_risk = min(math.log10(deal.deal_value + 1) / 10.0, 1.0)

        # Weighted combination
        raw_score = 0.4 * jurisdiction_risk + 0.3 * tax_risk + 0.3 * value_risk
        return min(max(raw_score, 0.0), 1.0)
