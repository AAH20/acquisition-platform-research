"""Export Control Compliance Module.

Assesses technology portfolios against ITAR (International Traffic in Arms
Regulations) and EAR (Export Administration Regulations) requirements,
computes compliance scores, evaluates cross-border deal risk, and generates
compliance reports with actionable recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.observability import get_logger, log_execution_time

logger = get_logger(__name__)


@dataclass
class ExportControlItem:
    """A technology item with export control classification flags."""

    technology_id: str
    name: str
    category: str
    itar: bool
    ear: bool
    dual_use: bool


@dataclass
class ComplianceResult:
    """Result of a compliance assessment over a portfolio of items."""

    items: list[ExportControlItem] = field(default_factory=list)
    compliance_score: float = 0.0
    risk_level: str = "low"
    recommendations: list[str] = field(default_factory=list)


class ExportControlAssessor:
    """Assesses export control compliance for technology portfolios.

    Evaluates items against ITAR/EAR regulations, computes a normalized
    compliance score, determines risk levels, assesses cross-border deal
    risk, checks ITEN (International Traffic in Arms Regulations Exemption)
    eligibility, and generates compliance reports.
    """

    # Risk level thresholds (score ranges)
    _CRITICAL_THRESHOLD: float = 0.25
    _HIGH_THRESHOLD: float = 0.50
    _MEDIUM_THRESHOLD: float = 0.75

    # Cross-border risk weights
    _ITAR_WEIGHT: float = 0.5
    _EAR_WEIGHT: float = 0.3
    _DUAL_USE_WEIGHT: float = 0.2

    # High-risk destination countries (embargoed / sanctioned)
    _HIGH_RISK_COUNTRIES: frozenset[str] = frozenset(
        {"CN", "RU", "IR", "KP", "SY", "CU"}
    )

    @log_execution_time(logger)
    def assess(
        self,
        technology_id: str,
        name: str,
        category: str,
        itar: bool,
        ear: bool,
        dual_use: bool,
    ) -> ExportControlItem:
        """Assess a single technology item for export control classification.

        Args:
            technology_id: Unique identifier for the technology.
            name: Human-readable name of the technology.
            category: Technology category (e.g., 'defense', 'software').
            itar: Whether the item is ITAR-controlled.
            ear: Whether the item is EAR-controlled.
            dual_use: Whether the item has dual-use applications.

        Returns:
            ExportControlItem with the classification flags.
        """
        return ExportControlItem(
            technology_id=technology_id,
            name=name,
            category=category,
            itar=itar,
            ear=ear,
            dual_use=dual_use,
        )

    @log_execution_time(logger)
    def compliance_score(self, items: list[ExportControlItem]) -> float:
        """Compute a normalized compliance score in [0, 1].

        The score is the fraction of items that are fully compliant
        (not ITAR, not EAR, not dual-use). An empty portfolio returns 0.0.

        Args:
            items: List of export control items to score.

        Returns:
            Compliance score between 0.0 (non-compliant) and 1.0 (fully compliant).
        """
        if not items:
            return 0.0

        compliant_count = sum(
            1 for item in items if not item.itar and not item.ear and not item.dual_use
        )
        return compliant_count / len(items)

    @log_execution_time(logger)
    def risk_level(self, score: float) -> str:
        """Determine risk level from a compliance score.

        Args:
            score: Compliance score in [0, 1].

        Returns:
            Risk level string: 'low', 'medium', 'high', or 'critical'.
        """
        if score < self._CRITICAL_THRESHOLD:
            return "critical"
        if score < self._HIGH_THRESHOLD:
            return "high"
        if score < self._MEDIUM_THRESHOLD:
            return "medium"
        return "low"

    @log_execution_time(logger)
    def cross_border_risk(self, items: list[ExportControlItem], target_country: str) -> float:
        """Assess cross-border deal risk for a target country.

        Risk is computed as a weighted combination of ITAR, EAR, and dual-use
        exposure, scaled by the risk profile of the destination country.

        Args:
            items: List of export control items in the deal.
            target_country: ISO country code of the destination.

        Returns:
            Risk score in [0, 1].
        """
        if not items:
            return 0.0

        # Base risk from item classifications
        itar_count = sum(1 for item in items if item.itar)
        ear_count = sum(1 for item in items if item.ear)
        dual_use_count = sum(1 for item in items if item.dual_use)

        n = len(items)
        base_risk = (
            self._ITAR_WEIGHT * (itar_count / n)
            + self._EAR_WEIGHT * (ear_count / n)
            + self._DUAL_USE_WEIGHT * (dual_use_count / n)
        )

        # Country risk multiplier
        country_multiplier = 1.5 if target_country.upper() in self._HIGH_RISK_COUNTRIES else 1.0

        return min(base_risk * country_multiplier, 1.0)

    @log_execution_time(logger)
    def iten_exemption(self, items: list[ExportControlItem]) -> bool:
        """Check if items are eligible for ITEN exemption.

        ITEN (International Traffic in Arms Regulations Exemption) is available
        only for items that are NOT ITAR-controlled. Any ITAR item disqualifies
        the entire portfolio.

        Args:
            items: List of export control items to check.

        Returns:
            True if all items are eligible for ITEN exemption, False otherwise.
        """
        if not items:
            return True
        return not any(item.itar for item in items)

    @log_execution_time(logger)
    def generate_report(self, items: list[ExportControlItem]) -> ComplianceResult:
        """Generate a full compliance report for a portfolio.

        Args:
            items: List of export control items to assess.

        Returns:
            ComplianceResult with score, risk level, and recommendations.
        """
        score = self.compliance_score(items)
        risk = self.risk_level(score)
        recommendations = self._generate_recommendations(items, score, risk)

        return ComplianceResult(
            items=list(items),
            compliance_score=score,
            risk_level=risk,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, items: list[ExportControlItem], score: float, risk_level: str
    ) -> list[str]:
        """Generate actionable compliance recommendations.

        Args:
            items: The assessed items.
            score: Computed compliance score.
            risk_level: Determined risk level.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []

        itar_items = [item for item in items if item.itar]
        ear_items = [item for item in items if item.ear]
        dual_use_items = [item for item in items if item.dual_use]

        if itar_items:
            recommendations.append(
                f"ITAR-controlled items detected ({len(itar_items)}): "
                "obtain DDTC license before export."
            )
        if ear_items:
            recommendations.append(
                f"EAR-controlled items detected ({len(ear_items)}): "
                "verify ECCN classification and obtain BIS license if required."
            )
        if dual_use_items:
            recommendations.append(
                f"Dual-use items detected ({len(dual_use_items)}): "
                "conduct end-use screening and maintain compliance records."
            )
        if risk_level == "critical":
            recommendations.append(
                "CRITICAL: Portfolio requires immediate compliance review "
                "before any cross-border transfer."
            )
        elif risk_level == "high":
            recommendations.append(
                "HIGH RISK: Enhanced due diligence required for cross-border deals."
            )
        elif risk_level == "medium":
            recommendations.append(
                "MEDIUM RISK: Standard export control procedures apply."
            )
        else:
            recommendations.append(
                "LOW RISK: Routine export control monitoring sufficient."
            )

        return recommendations
